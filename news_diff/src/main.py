from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['ir_lab_texts']
news_coll = db['news_texts']


def update_news_with(key, f):
    for doc in news_coll.find():
        if key not in doc:
            news_coll.update_one({'_id': doc['_id']}, {'$set': {key: f(doc)}})

# fix \xa0 spaces
# def fixed_doc_spaces(doc):
#     return doc['text'].replace(u'\xa0', u' ')
#
# for doc in news_coll.find():
#     news_coll.update_one({'_id': doc['_id']}, {'$set': {'text': fixed_doc_spaces(doc)}})


# ===== Preprocess text =====
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import pymorphy2

#nltk.download("stopwords")
tokenizer = RegexpTokenizer(r'\w+')
sw = stopwords.words('russian')
morph = pymorphy2.MorphAnalyzer()


def preprocess_text(text):
    words = tokenizer.tokenize(text.lower())
    normalized_words = [morph.parse(word)[0].normal_form for word in words]
    filtered_words = [word for word in normalized_words if word not in sw]
    pre_text = " ".join(filtered_words)
    return pre_text


def add_preprocess_to_doc(doc):
    return preprocess_text(doc['text'])

# update_news_with('pre_text', add_preprocess_to_doc)


# ===== Save duplicates to file =====
# def write_text(file, doc):
#     line = '{:9s}'.format(doc['source']) + ": " + doc['text'] + "\n"
#     file.write(line)
#
#
# duplicated_texts = list(news_coll.find({'duplicates': {'$ne': None}}))
# file = open("./Duplist.txt", "w", encoding='utf8')
#
# for text in duplicated_texts:
#     write_text(file, text)
#     for dup_id in text['duplicates']:
#         write_text(file, news_coll.find_one({'_id': dup_id}))
#     file.write("\n\n")
#
# file.close()


# ===== Find duplicates =====
import binascii
import re
import random
import time

max_shingle_value = 2 ** 32 - 1
next_prime = 4294967311  # prime number above max_shingle_id
shingle_size = 7
hashes_num = 50
duplicate_coeff = 0.7

def shingle_hash(a, b, shingle):
    return (a * shingle + b) % next_prime

def random_coeffs(k):
    rand_set = set()
    while len(rand_set) < k: rand_set.add(random.randint(0, max_shingle_value))
    return list(rand_set)

# Hash the shingle to a 32-bit integer.
def words_to_shingle(words):
    return binascii.crc32(' '.join(words).encode()) & 0xffffffff

def doc_to_shingles(doc_words):
    return set([words_to_shingle(doc_words[i:i + shingle_size])
                for i in range(0, len(doc_words) - shingle_size + 1)])

def doc_to_signature(coeffs_a, coeffs_b, doc_words):
    shingles = doc_to_shingles(doc_words)
    return [min([shingle_hash(coeffs_a[i], coeffs_b[i], sh) for sh in shingles])
            for i in range(hashes_num)]

def compare_docs_signatures(sig1, sig2):
    if len(sig1) == 0 or len(sig2) == 0:
        return 0

    if len(sig1) != len(sig2):
        print("wrong sigs:")
        print(sig1)
        print(sig2)
        raise Exception('Length of signatures must be equal!')

    same_amount = sum([1 if sig1[i] == sig2[i] else 0
                       for i in range(len(sig1))])

    return same_amount / hashes_num

def compare_docs_shingles(shingles1, shingles2):
    if len(shingles1) == 0 or len(shingles2) == 0:
        return 0

    same_amount = sum([1 if sh in shingles2 else 0 for sh in shingles1])

    return same_amount * 2 / (len(shingles1) + len(shingles2))

def get_docs_signatures(docs):
    coeffs_a = random_coeffs(hashes_num)
    coeffs_b = random_coeffs(hashes_num)
    return [doc_to_signature(coeffs_a, coeffs_b, doc)
            for doc in [d for d in docs if len(d) >= shingle_size]]

def get_docs_shingles(docs):
    return [doc_to_shingles(doc) for doc in [d if len(d) >= shingle_size else [] for d in docs]]

def find_duplicates_for_doc(f_compare, doc, docs):
    duplicates = {}
    for i in range(len(docs)):
        doc2 = docs[i]
        if doc2 is None or len(doc2) == 0:
            continue
        similarity = f_compare(doc, doc2)
        if similarity > duplicate_coeff:
            duplicates[i] = similarity
    return duplicates

def find_docs_duplicates(f_compare, docs):
    return {i: dups for (i, dups) in
            {i: find_duplicates_for_doc(f_compare, docs[i], [None] * (i+1) + docs[i+1:])
             for i in range(len(docs))}.items()
            if len(dups) > 0}

def flatten_duplicates_dict(duplicates_dict):
    return [[i1, i2, sim]
            for (i1, dups) in duplicates_dict.items()
            for (i2, sim) in dups.items()]

def remove_source_equals(duplicates_dict):
    duplicates_list = flatten_duplicates_dict(duplicates_dict)
    return [dup for dup in duplicates_list
            if news[dup[0]]["source"] != news[dup[1]]["source"]]

def print_docs_pairs(duplicates_list):
    for (i1, i2, sim) in duplicates_list:
        doc1 = news[i1].copy()
        doc2 = news[i2].copy()
        print(i1, ', ', i2, ', similarity: ', sim)
        print("Source: ", doc1["source"], "\n")
        print(doc1["text"])
        print("---")
        print("Source: ", doc2["source"], "\n")
        print(doc2["text"])
        print("\n\n======================================================\n\n")


news = list(news_coll.find())
corpus = [re.split(r"\s", x["pre_text"]) for x in news]

start_time = time.time()
docs_shingles = get_docs_shingles(corpus)
print('doc_to_shingles: ', time.time() - start_time)
# ==> 12.9025239944458

start_time = time.time()
docs_signatures = get_docs_signatures(corpus)
print('doc_to_sigs: ', time.time() - start_time)
# ==> 159.28504490852356 (2,6547 mins)

start_time = time.time()
duplicates_sig = find_docs_duplicates(compare_docs_signatures, docs_signatures)
print('sig dups: ', time.time() - start_time)
# ==> 2227,0844 (37,1180 mins)

start_time = time.time()
duplicates_sh = find_docs_duplicates(compare_docs_shingles, docs_shingles)
print('shingle dups: ', time.time() - start_time)
# ==> 5362.4713 (89,3745 mins)

duplicates1 = remove_source_equals(duplicates_sh)
duplicates2 = remove_source_equals(duplicates_sig)

print_docs_pairs(duplicates1)

