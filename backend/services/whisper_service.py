from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq()

def transcribe_audio(audio_path: str):
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file
        )

    return transcription.text
