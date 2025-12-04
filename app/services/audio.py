import os
import uuid
import shutil
from typing import Tuple, List
from gtts import gTTS
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import EncoderClassifier
import torch
import torchaudio

class AudioService:
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        
        print("Loading Whisper model...")
        # Use 'tiny' or 'base' for speed on CPU
        self.asr_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        
        print("Loading Speaker Encoder model...")
        # Downloads ~200MB model to ~/.cache/speechbrain
        self.speaker_model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/spkrec-ecapa-voxceleb",
            run_opts={"device": "cpu"}
        )

    async def save_upload_file(self, upload_file) -> str:
        file_path = os.path.join(self.upload_dir, f"{uuid.uuid4()}.wav")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return file_path

    async def transcribe(self, file_path: str) -> str:
        segments, info = self.asr_model.transcribe(file_path, beam_size=5)
        return " ".join([segment.text for segment in segments])

    async def get_speaker_embedding(self, file_path: str) -> Tuple[str, List[float]]:
        # Load audio
        signal, fs = torchaudio.load(file_path)
        
        # Generate embedding
        embeddings = self.speaker_model.encode_batch(signal)
        # embeddings shape: [batch, 1, 192]
        emb_vector = embeddings[0, 0].tolist()
        
        # Simple fingerprint (hash of the vector for now, or just uuid if not matching)
        # In real app, we search by vector similarity.
        # Here we return a random UUID as fingerprint_hash for the DB unique constraint,
        # but the embedding is real.
        fingerprint = str(uuid.uuid4()) 
        
        return fingerprint, emb_vector

    async def text_to_speech(self, text: str) -> str:
        tts = gTTS(text=text, lang='fr')
        filename = f"{uuid.uuid4()}.mp3"
        file_path = os.path.join(self.upload_dir, filename)
        tts.save(file_path)
        return file_path
