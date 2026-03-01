import streamlit as st
import base64
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import re
import time
from vosk import Model, KaldiRecognizer
import functools

load_dotenv()

# @functools.lru_cache(maxsize=1)
# def get_vosk_model(model_path):
#
#     return Model(model_path)



if 'page' not in st.session_state:
    st.session_state.page = 'home'

def welcome():

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


def recording():
    import os
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    from aiortc.contrib.media import MediaRecorder

    # Setup session state
    if "recording_started" not in st.session_state:
        st.session_state.recording_started = False

    collection_name = st.session_state.get('collectioName', 'Guest')
    if not os.path.exists("recordings"):
        os.makedirs("recordings")

    def recorder_factory():
        filename = f"recordings/audio_{collection_name}.wav"
        st.session_state.last_file = filename
        return MediaRecorder(filename)

    webrtc_ctx = webrtc_streamer(
        key="unique-recorder",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"audio": True, "video": False},
        in_recorder_factory=recorder_factory,
    )

    # --- Logic for handling the "Stop" event ---

    if webrtc_ctx.state.playing:
        st.session_state.recording_started = True
        st.warning("🔴 Recording... Click 'Stop' when finished.")

    # If it WAS recording but has now stopped:
    elif st.session_state.recording_started and not webrtc_ctx.state.playing:
        st.session_state.recording_started = False

        # Final check: Ensure the file exists before moving on
        if "last_file" in st.session_state and os.path.exists(st.session_state.last_file):
            st.success("Recording captured!")



def transcript_db():

    from faster_whisper import WhisperModel

    collection_name = st.session_state.get('collectioName', 'Guest')

    # 1. Load the model
    # Options: "tiny", "base", "small", "medium", "large-v3"
    model = WhisperModel("small", device="cpu", compute_type="int8")

    # 2. Transcribe
    segments, info = model.transcribe(f"recordings/audio_{collection_name}.wav", beam_size=5)

    print(f"Detected language: {info.language} with probability {info.language_probability:.2f}")

    # 3. Print segments as they are processed
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

        final_transcript = segment.text

    st.session_state["final_transcript"] = final_transcript

    # DataBase Initialization

    if "db_inserted" not in st.session_state:
        st.session_state.db_inserted = False

    if final_transcript and not st.session_state.db_inserted:
        mongo_uri = os.getenv("mongo_connector")
        client = MongoClient(mongo_uri)
        db = client['test_data']

        print(f"INSERTING TO DB: {final_transcript}")
        db[collection_name].insert_one({"Child_Answer": final_transcript})

        # Set the flag to True so it doesn't run again until reset
        st.session_state.db_inserted = True
    else:
        print("Skipping DB insertion: already inserted or empty.")

def child_response():

    import time
    from elevenlabs import ElevenLabs, VoiceSettings
    import os
    import pygame
    load_dotenv()

    eleven_api = os.getenv("ELEVENLABS_API_KEY")

    client = ElevenLabs(api_key=eleven_api)
    name = st.session_state.get('user_name', 'Guest')
    st.title(f"Hello {name}!")


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

    recording()

    # Define columns
    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        if st.button("Alphabets"):
            st.session_state["selected_subject"] = "Alphabets"
            font_style = """
            <style>
            .custom-font {
                font-family: 'Courier New', Courier, monospace; 
                color: #04471C; 
                background-color: #D4EDDA; 
                padding: 20px; 
                border-radius: 10px; 
                border: 1px solid #C3E6CB;
                font-size: 35px;
                font-weight: bold;
                text-align: center;
            }
            </style>
            """
            st.markdown(font_style, unsafe_allow_html=True)

            # Create single placeholders
            pygame.mixer.init()
            sound_file = "repeat after me.mp3"
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
            time.sleep(3)


            placeholder = st.empty()
            imageholder = st.empty()

            try:
                with open('alphabets.txt', 'r') as file:
                    for line in file:
                        text = line.strip()
                        if text:
                            # Update the SAME placeholders every time
                            placeholder.markdown(f'<div class="custom-font">{text}</div>', unsafe_allow_html=True)

                            # Added the 'f' prefix to correctly reference the variable
                            image_path = f"images/{text}.png"
                            imageholder.image(image_path)

                            audio = client.text_to_speech.convert(
                                text=text,
                                voice_id="MF3mGyEYCl7XYWbV9V6O",
                                model_id="eleven_v3",
                                voice_settings=VoiceSettings(
                                    stability=0.5,
                                    similarity_boost=0.85,
                                    style=0.0,
                                    use_speaker_boost=True
                                )
                            )

                            with open("response.mp3", "wb") as f:
                                for chunk in audio:
                                    f.write(chunk)

                            # display_clean_video("your_video.mp4")
                            pygame.mixer.init()
                            sound_file = "response.mp3"
                            pygame.mixer.music.load(sound_file)
                            pygame.mixer.music.play()

                            time.sleep(5)

                    placeholder.empty()
                    imageholder.empty()
                    st.success("Sequence complete!")


            except FileNotFoundError:
                st.error("File 'alphabets.txt' not found. Please check the file path.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.button("Submit and Save"):
        st.session_state.page = 'processing_page'
        st.rerun()

def ai_response():
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from dotenv import load_dotenv
    import os
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        api_key=api_key,
    )
    child_response = st.session_state.get("final_transcript", "No response captured.")


    # Define a prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """ we have dataset of which contains {dataset} like A For Apple.
        You are an expert educator for children age<5 years learning to pronounce specializing in {subject}. 
        Your task is to evaluate a student's response based on the following learning objectives: {learning_goals}.

        Provide a balanced critique in this format:
        1. **Strong Points**: What did the student grasp well?
        2. **Weak Points**: Where are the misconceptions or missing details?
        3. **Actionable Advice**: One specific tip to improve for next time.

        Use a {tone} tone that encourages the student."""),

        ("user", "Subject: {subject}\nStudent Response: {child_response}")
    ])

    # Create the chain
    chain = prompt | llm | StrOutputParser()

    # Invoke the chain
    # Invoke the chain with ALL required keys
    subject = st.session_state.get("selected_subject", "General")
    response = chain.invoke({
        "dataset": subject,
        "subject": subject,
        "learning_goals": "understanding of pronunciation of alphabets ",
        "tone": "encouraging and motivating",
        "child_response": child_response
    })

    st.title(response)

def process_saving():
    st.success("Saving And Building The Result")

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

    transcript_db()
    collection_name = st.session_state.get('collectioName', 'Guest')
    os.remove(f"recordings/audio_{collection_name}.wav")

    ai_response()

if st.session_state.page == 'home':
    welcome()
elif st.session_state.page == 'next_page':
    child_response()
elif st.session_state.page == 'processing_page':
    process_saving()
