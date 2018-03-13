#import pymongo
from pymongo import MongoClient
#from bson.objectid import ObjectId
#from importlib import reload

client = MongoClient('localhost', 27017)
db = client['test_db']
db_news = db['test_col']


def find_source_texts(source):
    return db_news.find({"source": source})


