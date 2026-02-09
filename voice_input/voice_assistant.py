import speech_recognition as sr


def listen_to_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        while True:
            print("Listening...")
            audio = r.listen(source)
            try:
                # command = r.recognize_google(audio).lower()
                command = r.recognize_sphinx(audio).lower()
                print(f"You said: {command}")
                if "exit" in command:
                    break
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError:
                print("API unavailable")


listen_to_voice()