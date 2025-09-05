import io
import requests
import string
from faster_whisper import WhisperModel

def transcribe_audio(url: str) -> str:
    audio = requests.get(url)
    if audio.status_code == 200:
        audio_data = io.BytesIO(audio.content)
        audio_data.name ="audio_captcha.mp3"

        model = WhisperModel(model_size_or_path = "distil-small.en", compute_type="float32")
    
        segments, info = model.transcribe(audio_data)
        result_text = " ".join([seg.text for seg in segments]).strip().lower()
        result_text = result_text.translate(str.maketrans('', '', string.punctuation))
        return result_text