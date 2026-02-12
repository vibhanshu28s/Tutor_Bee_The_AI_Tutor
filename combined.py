import streamlit as st
import base64
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import re
import time
from vosk import Model, KaldiRecognizer

model = Model("vosk-model-en-us-0.22")

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
                            time.sleep(3)

                        else:
                            db.create_collection(collection_name)
                            # Inserting a document ensures it's actually visible in MongoDB tools
                            db[collection_name].insert_one({"name": name.title(), "age": age})
                            st.success(f"WELCOME! {name.title()}")
                            time.sleep(3)

                        st.session_state['user_name'] = name.title()
                        st.session_state['user_age'] = age_input
                        st.session_state["collectioName"] = collection_name
                        st.session_state.page = "next_page"
                        st.rerun()  # This will now carry the data to the next page


                    except Exception as e:

                        st.error(f"Database Error: {e}")

    # return name, age_input
def  recording():
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    from aiortc.contrib.media import MediaRecorder

    def recorder_factory():
        return MediaRecorder("audio.wav")


    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    playing = st.session_state.get("playing", True)

    webrtc_ctx = webrtc_streamer(
        key="auto-save-recorder",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"audio": True, "video": False},
        in_recorder_factory=recorder_factory,
        desired_playing_state=playing,
    )

    if webrtc_ctx.state.playing:
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        elapsed_time = time.time() - st.session_state.start_time

        if elapsed_time < 10:
            time.sleep(0.5)
            st.rerun()
        else:
            st.session_state.playing = False
            st.session_state.start_time = None
            # st.rerun
def transcript_db():
    import os
    import json
    import wave

    wf = wave.open("output.wav", "rb")

    rec = KaldiRecognizer(model, wf.getframerate())

    full_text = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            full_text.append(result.get("text", ""))

    final_result = json.loads(rec.FinalResult())
    full_text.append(final_result.get("text", ""))

    print("FINAL TRANSCRIPT:")
    # print(" ".join(full_text))
    final_transcript = " ".join(full_text)

    # DataBase Initialization
    name = st.session_state.get('user_name', 'Guest')
    collection_name = st.session_state.get('collectioName', 'Guest')
    st.title(f"Hello {name}!")

    mongo_uri = os.getenv("mongo_connector")
    client = MongoClient(mongo_uri)
    db = client["test_data"]
    print(final_transcript)
    db[collection_name].insert_one({"Child_Answer": final_transcript})
    os.remove("output.wav")




if st.session_state.page == 'home':
    welcome()
# elif st.session_state.page == 'next_page':
#     child_response()
