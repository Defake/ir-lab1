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


# ===== Find duplicates =====
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

news = list(news_coll.find())
corpus = [x['pre_text'] for x in news]
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)
similarities_matrix = cosine_similarity(X)

sim_pairs = []
for x in range(len(similarities_matrix)):
    for y in range(x+1, len(similarities_matrix[x])):
        if 0.8 < similarities_matrix[x][y] < 1.0:
            if not news[x]['source'] == news[y]['source']:
                sim_pairs.append([x, y])

duplicates = {}
for a, b in sim_pairs:
    exact = False
    if a in duplicates:
        for text_i in duplicates[a]:
            if news[text_i]['text'] == news[b]['text']:
                exact = True
                break
    if not exact:
        duplicates.setdefault(a, []).append(b)
        duplicates.setdefault(b, []).append(a)

for key, value in duplicates.items():
    dup_ids = []
    for i in value:
        dup_ids.append(news[i]['_id'])
    news_coll.update_one({'_id': news[key]['_id']}, {'$set': {'duplicates': dup_ids}})


# ===== Save duplicates to file =====
def write_text(file, doc):
    line = '{:9s}'.format(doc['source']) + ": " + doc['text'] + "\n"
    file.write(line)


duplicated_texts = list(news_coll.find({'duplicates': {'$ne': None}}))
file = open("./Duplist.txt", "w", encoding='utf8')

for text in duplicated_texts:
    write_text(file, text)
    for dup_id in text['duplicates']:
        write_text(file, news_coll.find_one({'_id': dup_id}))
    file.write("\n\n")

file.close()
