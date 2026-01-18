import os
import uuid
import shutil
from typing import Tuple, List, Optional
from openai import AsyncOpenAI
from app.core.config import settings

class AudioService:
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        
        print(f"Initializing OpenAI Client for Audio (timeout={settings.OPENAI_TIMEOUT}s, retries={settings.OPENAI_MAX_RETRIES})...")
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT,
            max_retries=settings.OPENAI_MAX_RETRIES
        )
        
        # OpenAI Models
        self.stt_model = "whisper-1"
        self.tts_model = "tts-1"
        self.tts_voice = "nova"  # alloy, echo, fable, onyx, nova, shimmer
        
        # ADIA_TTS for Wolof (lazy loaded)
        self._adia_model = None
        self._adia_tokenizer = None
        self._adia_device = None

        # xTTS for Wolof (lazy loaded via GalsenAI)
        self._xtts_model = None
        self._xtts_latents = None
        self._xtts_device = None
        self._xtts_ref_audio = None

        # Wolof STT (dofbi/wolof-asr)
        self._wolof_stt_model = None
        self._wolof_stt_processor = None
        self._wolof_stt_device = None

        # Facebook MMS-LID for language detection (lazy loaded)
        self._mms_lid_model = None
        self._mms_lid_processor = None
        self._mms_lid_device = None

        # LAfricaMobile Service (lazy loaded)
        self._lafricamobile_service = None

    def _get_lafricamobile_service(self):
        if self._lafricamobile_service is None:
            from app.services.lafricamobile import LAfricaMobileService
            self._lafricamobile_service = LAfricaMobileService()
        return self._lafricamobile_service

    def _load_adia_tts(self):
        """Lazy load ADIA_TTS model for Wolof synthesis."""
        if self._adia_model is None:
            print("[Wolof] Loading ADIA_TTS model...")
            try:
                import torch
                from parler_tts import ParlerTTSForConditionalGeneration
                from transformers import AutoTokenizer
                
                self._adia_device = "cuda:0" if torch.cuda.is_available() else "cpu"
                self._adia_model = ParlerTTSForConditionalGeneration.from_pretrained(
                    "CONCREE/Adia_TTS"
                ).to(self._adia_device)
                self._adia_tokenizer = AutoTokenizer.from_pretrained("CONCREE/Adia_TTS")
                print(f"[Wolof] ADIA_TTS loaded on {self._adia_device}")
            except Exception as e:
                print(f"[Wolof] Failed to load ADIA_TTS: {e}")
                raise

    async def save_upload_file(self, upload_file) -> str:
        file_path = os.path.join(self.upload_dir, f"{uuid.uuid4()}.wav")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return file_path

    def _load_mms_lid(self):
        """Lazy load Facebook MMS-LID model for language identification."""
        if self._mms_lid_model is None:
            print("[LID] Loading Facebook MMS-LID-256 model...")
            try:
                from transformers import Wav2Vec2ForSequenceClassification, AutoFeatureExtractor
                import torch
                
                model_id = "facebook/mms-lid-256"
                self._mms_lid_device = "cuda" if torch.cuda.is_available() else "cpu"
                self._mms_lid_processor = AutoFeatureExtractor.from_pretrained(model_id)
                self._mms_lid_model = Wav2Vec2ForSequenceClassification.from_pretrained(model_id).to(self._mms_lid_device)
                
                print(f"[LID] MMS-LID loaded on {self._mms_lid_device}")
            except Exception as e:
                print(f"[LID] Failed to load MMS-LID: {e}")
                raise e

    async def _detect_language(self, file_path: str) -> Tuple[str, float]:
        """
        Detect language from audio using Facebook MMS-LID.
        Returns (language_code, confidence).
        Wolof = 'wol', French = 'fra', English = 'eng', etc.
        """
        import asyncio
        import librosa
        import torch
        import imageio_ffmpeg
        import subprocess
        
        self._load_mms_lid()
        
        def run_detection():
            # Convert audio to 16kHz mono WAV
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            temp_wav = f"{file_path}_lid.wav"
            
            try:
                cmd = [ffmpeg_path, "-y", "-i", file_path, "-ar", "16000", "-ac", "1", temp_wav]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                load_path = temp_wav
            except Exception as e:
                print(f"[LID] Audio conversion warning: {e}")
                load_path = file_path
            
            try:
                # Load audio
                audio, _ = librosa.load(load_path, sr=16000)
                print(f"[LID] Audio loaded: {len(audio)/16000:.1f}s duration")
                
                # Process
                inputs = self._mms_lid_processor(audio, sampling_rate=16000, return_tensors="pt")
                inputs = {k: v.to(self._mms_lid_device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self._mms_lid_model(**inputs).logits
                
                # Get prediction
                probs = torch.softmax(outputs, dim=-1)
                
                # Show top 5 detected languages for debugging
                top5_probs, top5_indices = torch.topk(probs[0], 5)
                print("[LID] ===== MMS-LID Detection Results =====")
                for i, (prob, idx) in enumerate(zip(top5_probs, top5_indices)):
                    lang_code = self._mms_lid_model.config.id2label[idx.item()]
                    is_wolof = " <-- WOLOF!" if lang_code == "wol" else ""
                    print(f"[LID]   #{i+1}: {lang_code} ({prob.item():.1%}){is_wolof}")
                print("[LID] ========================================")
                
                lang_id = torch.argmax(probs, dim=-1)[0].item()
                confidence = probs[0, lang_id].item()
                detected_lang = self._mms_lid_model.config.id2label[lang_id]
                
                # Explicit Wolof check
                if detected_lang == "wol":
                    print(f"[LID] ✓ WOLOF DETECTED with {confidence:.1%} confidence!")
                else:
                    print(f"[LID] ✗ Not Wolof. Detected: {detected_lang} ({confidence:.1%})")
                
                return detected_lang, confidence
            finally:
                if os.path.exists(temp_wav):
                    try:
                        os.remove(temp_wav)
                    except:
                        pass
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_detection)

    async def transcribe(self, file_path: str, forced_language: Optional[str] = None) -> Tuple[str, str]:
        """
        Transcribe audio with automatic language detection or forced language.
        Pipeline:
        1. If forced_language is provided, skip detection.
        2. Else, detect language with Facebook MMS-LID
        3. If Wolof (forced 'wo' or detected 'wol') -> use LAfricaMobile
        4. Otherwise -> use OpenAI Whisper with language parameter
        Returns (transcribed_text, language_code).
        """
        detected_lang = None
        confidence = 0.0
        
        if forced_language:
            print(f"[STT] Forced language: {forced_language}. Skipping detection.")
            # Map 'wo' to 'wol' for consistency with detection codes if needed, 
            # but we use 'wo' as our internal standard.
            target_lang = forced_language
        else:
            # Step 1: Detect language using MMS-LID
            try:
                detected_lang, confidence = await self._detect_language(file_path)
                print(f"[LID] Detected: {detected_lang} (confidence: {confidence:.1%})")
            except Exception as e:
                print(f"[LID] Language detection failed ({e}), defaulting to OpenAI Whisper...")
            target_lang = "wo" if detected_lang == "wol" else (detected_lang or "fr")

        # Step 2: Route based on target language
        if target_lang == "wo":
            print("[STT] Wolof target! Using LAfricaMobile API...")
            try:
                service = self._get_lafricamobile_service()
                text = await service.stt(file_path, lang="wolof")
                print(f"[STT] LAfricaMobile result: {text[:60]}...")
                return text, "wo"
            except Exception as e:
                print(f"[STT] LAfricaMobile failed ({e}), falling back to Whisper...")
        
        # Fallback to OpenAI Whisper
        print(f"[STT] Using OpenAI Whisper for language: {target_lang}...")
        
        # Map ISO-639-3 (3-letter) codes to ISO-639-1 (2-letter) for Whisper
        # Whisper only accepts ISO-639-1 codes
        ISO639_3_TO_1 = {
            "fra": "fr", "eng": "en", "ara": "ar", "spa": "es", "deu": "de",
            "ita": "it", "por": "pt", "rus": "ru", "jpn": "ja", "kor": "ko",
            "zho": "zh", "hin": "hi", "tur": "tr", "pol": "pl", "nld": "nl",
            "swe": "sv", "dan": "da", "nor": "no", "fin": "fi", "ces": "cs",
            "hun": "hu", "ron": "ro", "ell": "el", "heb": "he", "tha": "th",
            "vie": "vi", "ind": "id", "mal": "ms", "ukr": "uk", "cat": "ca",
            "aze": "az", "kaz": "kk", "uzb": "uz", "tat": "tt",
        }
        
        # Valid ISO-639-1 codes Whisper accepts (subset of common ones)
        VALID_WHISPER_LANGS = {
            "fr", "en", "ar", "es", "de", "it", "pt", "ru", "ja", "ko", 
            "zh", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi", "cs",
            "hu", "ro", "el", "he", "th", "vi", "id", "ms", "uk", "ca",
            "az", "kk", "uz"
        }
        
        # Convert 3-letter to 2-letter if needed
        lang_for_whisper = target_lang
        if target_lang and len(target_lang) == 3:
            lang_for_whisper = ISO639_3_TO_1.get(target_lang, None)
            if lang_for_whisper:
                print(f"[STT] Converted {target_lang} -> {lang_for_whisper}")
        
        with open(file_path, "rb") as audio_file:
            whisper_args = {
                "model": self.stt_model,
                "file": audio_file,
                "response_format": "verbose_json"
            }
            # Only pass language if it's a valid 2-letter code
            if lang_for_whisper and lang_for_whisper in VALID_WHISPER_LANGS:
                whisper_args["language"] = lang_for_whisper
            else:
                print(f"[STT] Language '{target_lang}' not in valid list, letting Whisper auto-detect")

            transcript = await self.client.audio.transcriptions.create(**whisper_args)
        
        text = transcript.text
        whisper_lang = getattr(transcript, 'language', lang_for_whisper or 'fr')
        
        print(f"[STT] Whisper result: lang={whisper_lang}, text={text[:60]}...")
        return text, whisper_lang

    async def get_speaker_embedding(self, file_path: str) -> Tuple[str, List[float]]:
        # Mock implementation - OpenAI doesn't provide speaker embeddings
        fingerprint = str(uuid.uuid4())
        emb_vector = [0.0] * 256
        return fingerprint, emb_vector

    async def text_to_speech(self, text: str, language: str = "fr") -> str:
        """
        Generate speech from text.
        Uses GalsenAI xTTS or ADIA_TTS for Wolof ('wo'), OpenAI TTS for others.
        Fallbacks: xTTS -> ADIA -> OpenAI.
        """
        import logging
        logger = logging.getLogger("uvicorn")
        logger.info(f"[TTS] Request - Language: {language}, Text length: {len(text)}")
        
        if language in ["wo", "wolof"]:
            # LAfricaMobile for Wolof
            logger.info("[TTS] Wolof detected, using LAfricaMobile API...")
            try:
                service = self._get_lafricamobile_service()
                # Use 'wolof' as language code for their API
                return await service.tts(text, lang="wolof")
            except Exception as e:
                # Fallback to OpenAI (or ADIA if we wanted deeper fallback hierarchy)
                logger.error(f"[TTS] LAfricaMobile failed ({e}), falling back to OpenAI TTS...")
                return await self._text_to_speech_openai(text)
        else:
            logger.info(f"[TTS] Using OpenAI TTS for language: {language}")
            return await self._text_to_speech_openai(text)

    async def _text_to_speech_openai(self, text: str) -> str:
        """Generate speech using OpenAI TTS API."""
        filename = f"{uuid.uuid4()}.mp3"
        file_path = os.path.join(self.upload_dir, filename)
        
        response = await self.client.audio.speech.create(
            model=self.tts_model,
            voice=self.tts_voice,
            input=text
        )
        
        response.stream_to_file(file_path)
        return file_path

    async def _text_to_speech_wolof(self, text: str) -> str:
        """Generate Wolof speech using ADIA_TTS (Parler-TTS)."""
        import asyncio
        
        # Load model if not already loaded
        self._load_adia_tts()
        
        filename = f"{uuid.uuid4()}.wav"
        file_path = os.path.join(self.upload_dir, filename)
        
        # Voice description for natural Wolof speech
        description = "A warm and natural voice, with a conversational flow"
        
        # ADIA_TTS has 200 char limit per inference, segment if needed
        segments = self._segment_text(text, max_chars=180)
        
        # Run TTS in thread pool to not block async
        def generate_audio():
            import torch
            import soundfile as sf
            import numpy as np
            
            all_audio = []
            
            for segment in segments:
                input_ids = self._adia_tokenizer(
                    description, return_tensors="pt"
                ).input_ids.to(self._adia_device)
                
                prompt_ids = self._adia_tokenizer(
                    segment, return_tensors="pt"
                ).input_ids.to(self._adia_device)
                
                with torch.no_grad():
                    audio = self._adia_model.generate(
                        input_ids=input_ids,
                        prompt_input_ids=prompt_ids,
                        temperature=0.8,
                        do_sample=True
                    )
                
                all_audio.append(audio.cpu().numpy().squeeze())
            
            # Concatenate all segments
            if len(all_audio) > 1:
                combined = np.concatenate(all_audio)
            else:
                combined = all_audio[0]
            
            # Save as WAV
            sf.write(file_path, combined, self._adia_model.config.sampling_rate)
            return file_path
        
        # Run in executor to not block event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, generate_audio)
        
        print(f"[Wolof] Generated TTS audio: {file_path}")
        return result

    def _segment_text(self, text: str, max_chars: int = 180) -> List[str]:
        """Segment text for ADIA_TTS which has 200 char limit."""
        if len(text) <= max_chars:
            return [text]
        
        segments = []
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        
        current_segment = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_segment) + len(sentence) + 2 <= max_chars:
                current_segment += (". " if current_segment else "") + sentence
            else:
                if current_segment:
                    segments.append(current_segment + ".")
                current_segment = sentence
        
        if current_segment:
            segments.append(current_segment + ".")
        
        return segments if segments else [text[:max_chars]]

    def _load_wolof_stt_model(self):
        """Lazy load dofbi/wolof-asr model."""
        if self._wolof_stt_model is None:
            print("[STT] Loading dofbi/wolof-asr model...")
            try:
                from transformers import WhisperForConditionalGeneration, WhisperProcessor
                import torch
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._wolof_stt_device = device
                
                model_name = "dofbi/wolof-asr"
                self._wolof_stt_processor = WhisperProcessor.from_pretrained(model_name)
                self._wolof_stt_model = WhisperForConditionalGeneration.from_pretrained(model_name).to(device)
                
                print(f"[STT] Wolof ASR model loaded on {device}")
            except Exception as e:
                print(f"[STT] Failed to load Wolof ASR: {e}")
                raise e

    async def _transcribe_wolof(self, file_path: str) -> Tuple[str, str]:
        """
        Transcribe using dofbi/wolof-asr (Whisper-based).
        Returns (transcription, 'wo').
        Language detection is handled by MMS-LID before this is called.
        """
        import asyncio
        import librosa
        import torch
        import imageio_ffmpeg
        import subprocess
        
        self._load_wolof_stt_model()
        
        def run_inference():
            # Conversion using imageio-ffmpeg binary to ensure compatibility (WebM -> WAV 16k)
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            temp_wav = f"{file_path}_16k.wav"
            
            try:
                # Convert explicitly to 16k mono wav
                cmd = [
                    ffmpeg_path, "-y", 
                    "-i", file_path, 
                    "-ar", "16000", 
                    "-ac", "1", 
                    temp_wav
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                load_path = temp_wav
            except Exception as e:
                print(f"[STT] Audio conversion fallback warning: {e}")
                load_path = file_path

            try:
                # Load audio at 16k
                audio_input, _ = librosa.load(load_path, sr=16000)
                
                input_features = self._wolof_stt_processor(
                    audio_input, 
                    return_tensors="pt", 
                    sampling_rate=16000
                ).input_features.to(self._wolof_stt_device)
                
                # Generate transcription
                with torch.no_grad():
                    predicted_ids = self._wolof_stt_model.generate(input_features)
                
                transcription = self._wolof_stt_processor.batch_decode(
                    predicted_ids, skip_special_tokens=True
                )[0]
                
                return transcription, "wo"
                
            finally:
                # Cleanup temp file
                if os.path.exists(temp_wav):
                    try:
                        os.remove(temp_wav)
                    except:
                        pass

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_inference)

    def _load_xtts_model(self):
        """Lazy load GalsenAI xTTS model."""
        if self._xtts_model is None:
            import sys
            import torch
            # Adjust path to the cloned repo
            repo_path = os.path.join(os.getcwd(), "libs", "Wolof-TTS", "notebooks", "Models", "xTTS v2")
            if repo_path not in sys.path:
                sys.path.append(repo_path)
            
            try:
                from TTS.tts.configs.xtts_config import XttsConfig
                from TTS.tts.models.xtts import Xtts
                
                checkpoint_dir = os.path.join(os.getcwd(), "uploads", "models", "xtts", "galsenai-xtts-wo-checkpoints")
                
                # Check for model existence (assume user extracted zip keeping structure)
                # We expect Anta_GPT_XTTS_Wo folder
                checkpoint_path = os.path.join(checkpoint_dir, "Anta_GPT_XTTS_Wo")
                model_path = os.path.join(checkpoint_path, "best_model_89250.pth")
                config_path = os.path.join(checkpoint_path, "config.json")
                vocab_path = os.path.join(checkpoint_dir, "XTTS_v2.0_original_model_files", "vocab.json")
                self._xtts_ref_audio = os.path.join(checkpoint_dir, "anta_sample.wav")
                
                if not os.path.exists(config_path):
                    raise FileNotFoundError(f"xTTS config not found at {config_path}. Did you unzip the model correctly into uploads/models/xtts?")
                
                print("[Wolof] Loading xTTS model...")
                config = XttsConfig()
                config.load_json(config_path)
                
                self._xtts_model = Xtts.init_from_config(config)
                self._xtts_model.load_checkpoint(config, checkpoint_path=model_path, vocab_path=vocab_path, use_deepspeed=False)
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._xtts_model.to(device)
                self._xtts_device = device
                
                print(f"[Wolof] xTTS model loaded on {device}!")
                
                # Pre-compute speaker latents
                if not os.path.exists(self._xtts_ref_audio):
                     print(f"[Wolof] Reference audio not found at {self._xtts_ref_audio}, checking root...")
                     # Try searching recursively? Or just warn.
                     raise FileNotFoundError(f"Reference audio missing: {self._xtts_ref_audio}")

                gpt_cond_latent, speaker_embedding = self._xtts_model.get_conditioning_latents(
                    audio_path=[self._xtts_ref_audio],
                    gpt_cond_len=self._xtts_model.config.gpt_cond_len,
                    max_ref_length=self._xtts_model.config.max_ref_len,
                    sound_norm_refs=self._xtts_model.config.sound_norm_refs
                )
                self._xtts_latents = (gpt_cond_latent, speaker_embedding)
                
            except Exception as e:
                print(f"[Wolof] Failed to load xTTS: {e}")
                raise e

    async def _text_to_speech_xtts(self, text: str) -> str:
        """Generate Wolof speech using GalsenAI xTTS."""
        import asyncio
        import logging
        logger = logging.getLogger("uvicorn")
        
        self._load_xtts_model()
        
        filename = f"{uuid.uuid4()}.wav"
        file_path = os.path.join(self.upload_dir, filename)
        
        def generate_audio():
            import soundfile as sf
            
            # Use pre-computed latents
            gpt_cond_latent, speaker_embedding = self._xtts_latents
            
            # Inference
            output = self._xtts_model.inference(
                text=text.lower(),
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                do_sample=False,
                speed=1.06,
                language="wo",
                enable_text_splitting=True
            )
            
            # Save audio
            sf.write(file_path, output['wav'], self._xtts_model.config.sampling_rate)
            return file_path

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, generate_audio)
        logger.info(f"[Wolof] Generated xTTS audio: {file_path}")
        return result
