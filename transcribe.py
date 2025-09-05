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
        print(result_text)
        return result_text


transcribe_audio("https://www.google.com/recaptcha/api2/payload?p=06AFcWeA5KYM-Vyp08AzQJ4p4sgn_bmPnnGlKGuOaqzoVPXbUw8Qb98GUWJSA4Nr1B_Dl7vcw2IvR9ueaYt8OX4V6wwr1aqmNYlAdlcxnbtsX8TYCYQ3kC4LwdlmQsRh0px1GL_1nlU-Y2QmKhDt6tscydcQM8EhK2PitaydwAKyOGGz9Uh1eVG_0ta_OzMq0PufArORAnmN8iCQ8Nk-8FaqyY57mGBkxtGw&k=6LfUFE0UAAAAAGoVniwSC9-MtgxlzzAb5dnr9WWY")