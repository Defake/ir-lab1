import random
import re

# path = "./Dict/zalizniak.txt"
# file = open(path, "r+", encoding='Windows-1251')
# odict = file.read().split('\n')
# file.close()
#
# path2 = "./Dict/odict.csv"
# file2 = open(path2, "r+", encoding='Windows-1251')
# wforms = file2.read().split('\n')
# file2.close()

path_corp = "./Dict/dict.opcorpora.txt"
file_corp = open(path_corp, "r+", encoding='utf8')
corp_text = file_corp.read()
file_corp.close()

corp = [x for x in re.split('\d+\n', corp_text) if re.search("\w", x)]

mapping = {'ADJF': 'A',
           'ADJS': 'A',
           'ADVB': 'ADV',
           'COMP': 'A',
           'CONJ': 'CONJ',
           'GRND': 'V',
           'INFN': 'V',
           'INTJ': 'ADV',
           'NOUN': 'S',
           'NPRO': 'A',
           'NUMR': 'NI',
           'PRCL': 'ADV',
           'PRED': 'ADV',
           'PREP': 'PR',
           'PRTF': 'V',
           'PRTS': 'V',
           'VERB': 'V'}

wdict = {}

i = 0
for s in corp:
    forms = s.split('\n')
    m = re.search('(\w+)\t(\w+)', forms[0])
    if m is None:
        continue
    word = m.group(1).lower().replace('ё', 'е')
    tag = mapping[m.group(2)]
    if word not in wdict:
        wdict[word] = [word, tag]
    for form in forms[1:]:
        m = re.search('(\w+)\t', form)
        if m is not None:
            word_form = m.group(1).lower().replace('ё', 'е')
            if word_form not in wdict:
                wdict[word_form] = [word, tag]
    i+=1

def tokenize(word):
    wordl = word.lower().replace('ё', 'е')
    if wordl in wdict:
        token = wdict[wordl]
        return word + "{" + token[0] + "=" + token[1] + "}"
    else:
        return word + "{" + wordl + "=S}"

def process_text(text):
    sentences = text.split('\n')
    tokens = ""
    for s in sentences:
        words = re.findall("\w+", s)
        tokens += " ".join([tokenize(w) for w in words])
        tokens += "\n"
    return tokens

path = "/Users/defake/Downloads/dataset_37845_1(2).txt"
file = open(path, "r+", encoding='utf-8')
datatext = file.read()
file.close()

p = process_text(datatext)

len(re.findall("\w+", datatext))
len(re.findall("\w+\{\w+=\w+\}", p))

re.findall("\w+\{\w+=\w+\}", "Она{она=S} Он{он=S}")

file_res = open("./res.txt", "w+", encoding='utf-8')
file_res.write(p)
file_res.close()
