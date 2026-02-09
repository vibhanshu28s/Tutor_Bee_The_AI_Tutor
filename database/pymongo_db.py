import pymongo 
import os
from dotenv import load_dotenv

load_dotenv()


def load_database():
    mongo_db = os.getenv("mongo_connector")
    myclient = pymongo.MongoClient(mongo_db)
    mydb = myclient["child_data"]

