from pymongo import MongoClient

client = MongoClient('localhost',27017)
db = client.bilibili
video = db.video

def insert_video(v):
    #  # bson.errors.InvalidDocument: key 'https://b23.tv/bveMkV' must not contain '.'
    # https://stackoverflow.com/questions/28664383/mongodb-not-allowing-using-in-key
    # insert_one 上的 bypass_document_validation=True 无效
    # 使用 insert ,check_keys=False 可以插入，但是insert已经过期
    video.insert(v,check_keys=False)
