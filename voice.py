import os
import wave
import io
from google.cloud import speech_v1 as speech
from streamlit_mic_recorder import mic_recorder
import streamlit as st

class VoiceProcessor:
    def __init__(self, credentials_path="ai-interview-54321-c85b0cb75e26.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.client = speech.SpeechClient()
        self.silence_duration=3.0
        
    
    def _get_wav_sample_rate(self, audio_bytes):
        """Detects sample rate from WAV header"""
        with io.BytesIO(audio_bytes) as wav_file:
            with wave.open(wav_file, 'rb') as wav:
                return wav.getframerate()

    def record_audio(self, key_suffix=""):
        """Record audio with automatic sample rate detection"""
        audio = mic_recorder(
            start_prompt="🎙️ Start Recording",
            stop_prompt="⏹️ Stop Recording",
            format="wav",
            key=f"recorder_{key_suffix}"
        )
        if audio and audio['bytes']:
            # Convert to correct sample rate if needed
            sample_rate = self._get_wav_sample_rate(audio['bytes'])
            return {
                'bytes': audio['bytes'],
                'sample_rate': sample_rate
            }
        return None

    def transcribe_audio(self, audio_data):
        """Transcribe audio with automatic sample rate configuration"""
        try:
            audio = speech.RecognitionAudio(content=audio_data['bytes'])
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=audio_data['sample_rate'],  # Use detected rate
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            response = self.client.recognize(config=config, audio=audio)
            return response.results[0].alternatives[0].transcript.strip() if response.results else ""
        except Exception as e:
            st.error(f"Transcription error: {e}")
            return ""

# import whisper
# import io
# import wave
# from streamlit_mic_recorder import mic_recorder
# import streamlit as st

# class VoiceProcessor:
#     def __init__(self, model="base"):
#         """Load Whisper model (tiny, base, small, medium, large)"""
#         self.model = whisper.load_model(model)
#         self.silence_duration = 3.0

#     def _get_wav_sample_rate(self, audio_bytes):
#         """Detects sample rate from WAV header"""
#         with io.BytesIO(audio_bytes) as wav_file:
#             with wave.open(wav_file, 'rb') as wav:
#                 return wav.getframerate()

#     def record_audio(self, key_suffix=""):
#         """Record audio with automatic sample rate detection"""
#         audio = mic_recorder(
#             start_prompt="🎙️ Start Recording",
#             stop_prompt="⏹️ Stop Recording",
#             format="wav",
#             key=f"recorder_{key_suffix}"
#         )
#         if audio and audio['bytes']:
#             sample_rate = self._get_wav_sample_rate(audio['bytes'])
#             return {
#                 'bytes': audio['bytes'],
#                 'sample_rate': sample_rate
#             }
#         return None

#     def transcribe_audio(self, audio_data):
#         """Transcribe audio using local Whisper model"""
#         try:
#             if not audio_data:
#                 return ""
            
#             # Save to a temporary file (Whisper needs a file path)
#             with open("temp_audio.wav", "wb") as f:
#                 f.write(audio_data['bytes'])
            
#             # Transcribe
#             result = self.model.transcribe("temp_audio.wav")
#             return result["text"].strip()
        
#         except Exception as e:
#             st.error(f"Transcription error: {e}")
#             return ""