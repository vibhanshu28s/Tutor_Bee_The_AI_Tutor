import streamlit as st
from welcome_name import welcome
import os
from dotenv import load_dotenv
from pymongo import MongoClient


# Check if we already have the user data from the welcome process
if 'user_name' in st.session_state:
    name = st.session_state['user_name']
    age = st.session_state['user_age']
else:
    # If a user tries to access this page directly, send them to welcome
    st.warning("Please complete the welcome step first!")
    name, age = welcome() # Or redirect them

st.title("Welcome to Working Page")

load_dotenv()
mongo_uri = os.getenv("mongo_connector")
client = MongoClient(mongo_uri)
db = client["test_data"]
clean_name = name.strip().replace(" ", "_")
collection_name = f"{clean_name}_{age}"
db[collection_name].insert_one({"name" : name, "age" : age})
# # print(collection_Name)
#
#
# def child_response():
#     import queue
#     import sounddevice as sd
#     import json
#     from vosk import Model, KaldiRecognizer
#
#     q = queue.Queue()
#
#     def callback(indata, frames, time, status):
#         q.put(bytes(indata))
#
#     model = Model("vosk-model-en-us-0.22")
#     rec = KaldiRecognizer(model, 16000)
#
#
#     with sd.RawInputStream(
#         samplerate=16000,
#         blocksize=8000,
#         dtype="int16",
#         channels=1,
#         callback=callback
#     ):
#         print("Speak now...")
#
#         while True:
#             data = q.get()
#             if rec.AcceptWaveform(data):
#                 result = json.loads(rec.Result())
#                 print("Child said:", result["text"])
