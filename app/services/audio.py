import os
import uuid
import shutil
from typing import Tuple, List
from gtts import gTTS
from faster_whisper import WhisperModel

# NOTE: Speechbrain disabled due to torchaudio 2.9.1 incompatibility
# TODO: Fix by downgrading torchaudio or updating speechbrain when compatible
# from speechbrain.inference.speaker import EncoderClassifier
# import torch
# import torchaudio

class AudioService:
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        
        print("Loading Whisper model...")
        # Use 'tiny' or 'base' for speed on CPU
        self.asr_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        
        # Speechbrain speaker encoder disabled - using mock
        print("Speaker identification: Using mock (speechbrain disabled)")
        self.speaker_model = None

    async def save_upload_file(self, upload_file) -> str:
        file_path = os.path.join(self.upload_dir, f"{uuid.uuid4()}.wav")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return file_path

    async def transcribe(self, file_path: str) -> str:
        segments, info = self.asr_model.transcribe(file_path, beam_size=5)
        return " ".join([segment.text for segment in segments])

    async def get_speaker_embedding(self, file_path: str) -> Tuple[str, List[float]]:
        # Mock implementation - returns random fingerprint and zero embedding
        # Real implementation would use speechbrain when torchaudio is compatible
        fingerprint = str(uuid.uuid4())
        # Return a mock 256-dimensional embedding (matches DB schema)
        emb_vector = [0.0] * 256
        return fingerprint, emb_vector

    async def text_to_speech(self, text: str) -> str:
        tts = gTTS(text=text, lang='fr')
        filename = f"{uuid.uuid4()}.mp3"
        file_path = os.path.join(self.upload_dir, filename)
        tts.save(file_path)
        return file_path

