import streamlit as st
import base64
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import re

load_dotenv()

if 'page' not in st.session_state:
    st.session_state.page = 'home'

def welcome():
    # Placing Bacground Image.

    def get_base64_of_bin_file(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    def set_png_as_page_bg(bin_file):
        bin_str = get_base64_of_bin_file(bin_file)
        page_bg_img = f'''
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            '''
        st.markdown(page_bg_img, unsafe_allow_html=True)

    set_png_as_page_bg('static/background.png')

    # TextBox Placement
    input_style = """
        <style>
            /* 1. Main container centering */
            [data-testid="stVerticalBlock"] {
                align-items: center;
                justify-content: center;
                text-align: center;
            }

            /* 2. Styling the label with your chosen font/color */
            label[data-testid="stWidgetLabel"] p {
                font-family: 'Comic Sans MS', cursive, sans-serif; 
                font-size: 24px !important;                      
                font-weight: bold;                               
                color: #FF8C00;                                  
                display: flex;
                justify-content: center;
            }

            /* 3. Adjusting the width of the input box */
            div[data-testid="stTextInput"] {
                width: 100%;
                max-width: 450px;
                margin: 0 auto;
            }

            /* 4. Centering the success message text */
            div[data-testid="stNotification"] {
                display: flex;
                justify-content: center;
                width: max-content;
                margin: 10px auto;
            }
        </style>
        """

    st.markdown(input_style, unsafe_allow_html=True)

    # Using columns to keep horizontal center and pushing data into database
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.write("##")
        st.write("##")
        st.write("##")
        st.write("##")
        st.write("##")
        st.write("##")
        st.write("##")

        name = st.text_input("Type in all your names, even the middle ones!", placeholder="Full Name")
        age_input = st.text_input("Age Also!", placeholder="Age")

        if st.button("Submit"):
            # 1. Basic empty check
            if not name or not age_input:
                st.error("Both Name and Age are required!")

            else:
                # 2. Validate Name (Letters and spaces only)
                if not name.replace(" ", "").isalpha():
                    st.error("Name must only contain alphabetical letters.")

                # 3. Validate Age (Must be exactly 1 or 2 digits)
                # ^\d{1,2}$ means: start of string, digit, between 1 and 2 times, end of string
                elif not re.match(r"^\d{1,2}$", age_input):
                    st.error("Age must be a 1 or 2 digit number (0-99).")

                else:
                    # If both pass, proceed to MongoDB
                    try:
                        age = int(age_input)
                        # load_dotenv()
                        mongo_uri = os.getenv("mongo_connector")
                        client = MongoClient(mongo_uri)
                        db = client["test_data"]

                        # Sanitize collection name
                        clean_name = name.strip().replace(" ", "_")
                        collection_name = f"{clean_name}_{age}"

                        if collection_name in db.list_collection_names():
                            st.success(f"Welcome Back! {name.title()}")

                        else:
                            db.create_collection(collection_name)
                            # Inserting a document ensures it's actually visible in MongoDB tools
                            db[collection_name].insert_one({"name": name.title(), "age": age})
                            st.success(f"WELCOME! {name.title()}")

                        st.session_state['user_name'] = name.title()
                        st.session_state['user_age'] = age_input
                        st.session_state["collectioName"] = collection_name
                        st.session_state.page = "next_page"
                        st.rerun()  # This will now carry the data to the next page

                    except Exception as e:

                        st.error(f"Database Error: {e}")

    # return name, age_input


def child_response():
    import queue
    import sounddevice as sd
    import json
    from vosk import Model, KaldiRecognizer

    # 1. Reset alignment and background styles immediately
    reset_style = """
        <style>
            [data-testid="stAppViewContainer"] {
                background-image: none !important; /* Clears the old BG if new one fails */
            }
            [data-testid="stVerticalBlock"] {
                align-items: flex-start !important;
                justify-content: flex-start !important;
                text-align: left !important;
            }
        </style>
    """
    st.markdown(reset_style, unsafe_allow_html=True)

    # 2. Set the new background
    def get_base64_of_bin_file(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    def set_png_as_page_bg(bin_file):
        bin_str = get_base64_of_bin_file(bin_file)
        page_bg_img = f'''
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/png;base64,{bin_str}") !important;
                background-size: cover !important;
            }}
            </style>
            '''
        st.markdown(page_bg_img, unsafe_allow_html=True)

    set_png_as_page_bg('static/workking_background.png')

    # 3. UI Content
    name = st.session_state.get('user_name', 'Guest')
    collection_name = st.session_state.get('collectioName', 'Guest')
    st.title(f"Hello {name}!")

    mongo_uri = os.getenv("mongo_connector")
    client = MongoClient(mongo_uri)
    db = client["test_data"]

    # 4. Use a button to start the loop so the UI can render first
    if st.button("Start Mic"):
        q = queue.Queue()

        def callback(indata, frames, time, status):
            q.put(bytes(indata))

        model = Model("vosk-model-en-us-0.22")
        rec = KaldiRecognizer(model, 16000)

        with sd.RawInputStream(
                samplerate=16000, blocksize=8000, dtype="int16",
                channels=1, callback=callback
        ):
            st.info("Mic is active. Speak now...")
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    # Displaying in the app instead of just the terminal
                    st.write(f"You said: {result['text']}")
                    db[collection_name].insert_one({"You_Said": result['text'] })
                    print(result['text'])





if st.session_state.page == 'home':
    welcome()
elif st.session_state.page == 'next_page':
    child_response()
