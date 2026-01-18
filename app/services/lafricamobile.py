import httpx
import os
import uuid
import logging
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger("uvicorn")

class LAfricaMobileService:
    def __init__(self):
        self.base_url = settings.LAFRICAMOBILE_BASE_URL
        self.username = settings.LAFRICAMOBILE_USERNAME
        self.password = settings.LAFRICAMOBILE_PASSWORD
        self.token = None
        self.client = httpx.AsyncClient(timeout=60.0)
        self.upload_dir = settings.UPLOAD_DIR

    async def _authenticate(self):
        """Authenticate and retrieve access token"""
        if not self.username or not self.password:
            logger.error("[LAfricaMobile] Missing credentials")
            raise ValueError("LAfricaMobile credentials not configured")
            
        try:
            logger.info("[LAfricaMobile] Authenticating...")
            response = await self.client.post(
                f"{self.base_url}/login",
                data={
                    "username": self.username,
                    "password": self.password,
                    "grant_type": "password" 
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            logger.info("[LAfricaMobile] Authentication successful")
        except Exception as e:
            logger.error(f"[LAfricaMobile] Authentication failed: {e}")
            raise e

    async def _get_headers(self):
        if not self.token:
            await self._authenticate()
        return {"Authorization": f"Bearer {self.token}"}

    async def stt(self, file_path: str, lang: str = "wolof") -> str:
        """
        Perform Speech-to-Text.
        Returns the transcription text.
        """
        import imageio_ffmpeg
        import subprocess
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        headers = await self._get_headers()
        # Remove Content-Type from headers as multipart/form-data boundary is handled by client
        if "Content-Type" in headers:
            headers.pop("Content-Type", None)
            
        # Convert to 16kHz Mono WAV to ensure compatibility
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        converted_path = f"{file_path}_clean.wav"
        
        try:
            # Convert
            subprocess.run(
                [ffmpeg_path, "-y", "-i", file_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", converted_path], 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            with open(converted_path, "rb") as f:
                # Send as standard WAV
                files = {"audio": (os.path.basename(converted_path), f, "audio/wav")}
                data = {"to_lang": lang}
                
                logger.info(f"[LAfricaMobile] Sending STT request for {os.path.basename(converted_path)} (16kHz WAV)...")
                
                response = await self.client.post(
                    f"{self.base_url}/stt/",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 401: # Token expired
                    await self._authenticate()
                    headers = await self._get_headers()
                    if "Content-Type" in headers:
                        headers.pop("Content-Type", None)
                        
                    # Reset file pointer for retry
                    f.seek(0)
                    response = await self.client.post(
                        f"{self.base_url}/stt/",
                        headers=headers,
                        files=files,
                        data=data
                    )
                
                if response.status_code != 200:
                    logger.error(f"[LAfricaMobile] API Error: {response.text}")
                    
                response.raise_for_status()
                result = response.json()
                logger.info(f"[LAfricaMobile] STT Result: {result}")
                
                # Check for transcription key
                if "transcription" in result:
                     return result["transcription"]
                else:
                     logger.warning(f"[LAfricaMobile] Unexpected response format: {result}")
                     return ""
                     
        except Exception as e:
            logger.error(f"[LAfricaMobile] STT failed: {e}")
            raise e
        finally:
            # Clean up converted file
            if os.path.exists(converted_path):
                try:
                    os.remove(converted_path)
                except:
                    pass

    async def translate(self, text: str, to_lang: str) -> str:
        """
        Translate text.
        """
        headers = await self._get_headers()
        payload = {
            "text": text,
            "to_lang": to_lang
        }
        
        try:
            logger.info(f"[LAfricaMobile] Translating '{text[:20]}...' to {to_lang}")
            response = await self.client.post(
                f"{self.base_url}/tts/translate",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 401:
                await self._authenticate()
                headers = await self._get_headers()
                response = await self.client.post(
                    f"{self.base_url}/tts/translate",
                    headers=headers,
                    json=payload
                )

            response.raise_for_status()
            result = response.json()
            return result.get("translated_text", text) # fallback to original if key missing
        except Exception as e:
            logger.error(f"[LAfricaMobile] Translation failed: {e}")
            # Fallback to returning original text if translation fails, or raise?
            # Raising is better so we can fallback to other methods if needed
            raise e

    async def tts(self, text: str, lang: str = "wolof") -> str:
        """
        Perform Text-to-Speech.
        Returns the local path of the generated audio file.
        """
        headers = await self._get_headers()
        payload = {
            "text": text,
            "to_lang": lang,
            "pitch": 0.0,
            "speed": 1.0
        }
        
        try:
            logger.info(f"[LAfricaMobile] Requesting TTS for '{text[:20]}...'")
            response = await self.client.post(
                f"{self.base_url}/tts/",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 401:
                await self._authenticate()
                headers = await self._get_headers()
                response = await self.client.post(
                    f"{self.base_url}/tts/",
                    headers=headers,
                    json=payload
                )
            
            response.raise_for_status()
            result = response.json()
            remote_audio_url = result.get("path_audio")
            
            if not remote_audio_url:
                raise ValueError("No audio path returned from API")

            # Download the audio file
            return await self._download_audio(remote_audio_url)
            
        except Exception as e:
            logger.error(f"[LAfricaMobile] TTS failed: {e}")
            raise e

    async def _download_audio(self, url: str) -> str:
        """Download audio from URL to local uploads directory"""
        try:
            # Handle relative or absolute URL if needed (docs show just path string)
            # Assuming it might be a full URL or relative to some base.
            # If the API returns a full URL, use it. If relative, prepend base_url (maybe?)
            # The doc says "path_audio": "<string>", possibly a full URL.
            # Let's assume it's a URL for now.
            
            # Use UUID for local filename
            ext = os.path.splitext(url)[1] or ".wav" # default to wav if no extension
            filename = f"{uuid.uuid4()}{ext}"
            file_path = os.path.join(self.upload_dir, filename)
            
            logger.info(f"[LAfricaMobile] Downloading audio from {url} to {file_path}")
            
            async with self.client.stream("GET", url) as response:
                 response.raise_for_status()
                 with open(file_path, "wb") as f:
                     async for chunk in response.aiter_bytes():
                         f.write(chunk)
            
            return file_path
        except Exception as e:
            logger.error(f"[LAfricaMobile] Failed to download audio: {e}")
            raise e

    async def close(self):
        await self.client.aclose()
