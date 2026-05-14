from .model_manager import model_manager

def transcribe_audio(audio_path: str):
    return model_manager.get_transcription(audio_path)
