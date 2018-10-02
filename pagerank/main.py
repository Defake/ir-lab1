import os
import numpy as np
from collections import Counter
from sklearn.metrics.pairwise import euclidean_distances

def get_file_content(fpath, enc='utf-8'):
    file = open(fpath, "r", encoding=enc)
    content = file.read()
    file.close()
    return content.split('\n')

def get_page_links(page_file_name):
    return [link.strip() for link in get_file_content(os.path.join(r'./links', page_file_name))]

def get_ranked_pages(page_names, links_by_index):
    index_by_page = dict(zip(page_names, range(len(page_names))))
    matrix = np.zeros((len(page_names), len(page_names)))

    for page, page_i in index_by_page.items():
        links = links_by_index[page_i]
        counter = Counter(links)
        for link in links:
            matrix[page_i][index_by_page[link]] = counter[link] / len(links)

    matrix = np.array(matrix)
    matrix += 0.00001
    matrix /= (matrix.max()+0.05)
    rank = np.random.normal(size=len(page_names))
    while True:
        prev_rank = rank
        rank = matrix.T.dot(rank)
        if euclidean_distances(prev_rank.reshape(1, -1), rank.reshape(1, -1)) < 1e-6:
            break
    return rank

def get_request_result(page_names, rank, amount, request=""):
    index_by_page = dict(zip(page_names, range(len(page_names))))
    page_names = np.array(page_names)

    request_pages_ix = np.array([i for page, i in index_by_page.items()
                                 if request == "" or request.lower() in page.lower()])
    request_rank = rank[request_pages_ix]
    ranked_pages_ix = request_pages_ix[(-request_rank).argsort()]
    return list(page_names[ranked_pages_ix][:amount])

fnames = os.listdir(r'./links')
pages = [page.rsplit('.', 1)[0] for page in fnames]
pages_links = [[link for link in get_page_links(fname)
                if link in pages]
               for fname in fnames]

pagerank = get_ranked_pages(pages, pages_links)

get_request_result(pages, pagerank, 20)
# ==>
# ['США',
#  'Великобритания',
#  'Франция',
#  'СССР',
#  'Германия',
#  'XX_век',
#  'Большая_советская_энциклопедия',
#  'Лондон',
#  'XIX_век',
#  'Москва',
#  'Европа',
#  'Италия',
#  'Канада',
#  'Англия',
#  'Испания',
#  'Викисклад',
#  'Япония',
#  'Индия',
#  '2009_год',
#  '2002_год']

get_request_result(pages, pagerank, 20, "армстронг")
# ==>
# ['Армстронг,_Луи',
#  'Армстронг,_Билли_Джо',
#  'Армстронг,_Нил',
#  'Армстронг,_Эдвин',
#  'Армстронг,_Нил_Олден',
#  'Билли_Джо_Армстронг',
#  'Армстронг_(фамилия)',
#  'Армстронг,_Лэнс',
#  'Армстронг,_Алан',
#  'Клан_Армстронг',
#  'Армстронг,_Уильям_Джордж',
#  'Армстронг,_Роберт',
#  'Армстронг,_Артур_Хилари',
#  'Армстронг_(округ,_Техас)',
#  'Армстронг,_Бесс',
#  'Армстронг,_Джиллиан',
#  'Армстронг,_Даррелл',
#  'Армстронг,_Дебби',
#  'Армстронг,_Скотт_(баскетболист)',
#  'Армстронг,_Генри_Эдвард']
