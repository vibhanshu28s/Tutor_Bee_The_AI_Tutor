import speech_recognition as sr

# Create a Recognizer object
r = sr.Recognizer()

# Use the default microphone as the audio source
with sr.Microphone() as source:
    print("Listening... Speak something!")
    # Adjust for ambient noise levels to improve accuracy
    r.adjust_for_ambient_noise(source, duration=1)
    # Listen for the audio input
    audio = r.listen(source)
    print("Audio captured. Processing...")

try:
    # Use Google Web Speech API to convert audio to text
    text = r.recognize_google(audio, language='en-US')
    print(f"You said: {text}")

except sr.UnknownValueError:
    # Handle cases where the speech is unintelligible
    print("Sorry, could not understand the audio.")
except sr.RequestError as e:
    # Handle API errors (e.g., no internet connection, quota limits)
    print(f"Could not request results from Google Speech Recognition service; {e}")

