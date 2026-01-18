import json
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings

# Define appointment-related tools for OpenAI
APPOINTMENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": "Recherche des médecins disponibles par spécialité. Utilisez cette fonction quand l'utilisateur veut prendre un rendez-vous et mentionne une spécialité ou demande les médecins disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {
                        "type": "string",
                        "description": "Nom de la spécialité médicale recherchée (ex: cardiologie, pédiatrie, dermatologie)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_slots",
            "description": "Obtient les créneaux de rendez-vous disponibles pour un médecin ou une spécialité à une date donnée.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {
                        "type": "string",
                        "description": "ID du médecin (optionnel si specialty est fourni)"
                    },
                    "specialty": {
                        "type": "string", 
                        "description": "Spécialité médicale (optionnel si doctor_id est fourni)"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date souhaitée au format YYYY-MM-DD"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Réserve un rendez-vous pour le patient. Utilisez cette fonction uniquement quand vous avez toutes les informations nécessaires: médecin, date, heure, nom du patient, email et motif.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {
                        "type": "string",
                        "description": "ID du médecin"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date du rendez-vous au format YYYY-MM-DD"
                    },
                    "time": {
                        "type": "string",
                        "description": "Heure du rendez-vous au format HH:MM"
                    },
                    "patient_name": {
                        "type": "string",
                        "description": "Nom complet du patient"
                    },
                    "patient_email": {
                        "type": "string",
                        "description": "Email du patient"
                    },
                    "patient_phone": {
                        "type": "string",
                        "description": "Téléphone du patient (optionnel)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Motif de la consultation"
                    }
                },
                "required": ["doctor_id", "date", "time", "patient_name", "patient_email", "reason"]
            }
        }
    }
]

class LLMService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            print(f"Initializing OpenAI Client for LLM (timeout={settings.OPENAI_TIMEOUT}s, retries={settings.OPENAI_MAX_RETRIES})...")
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
            self.model = settings.OPENAI_MODEL
        else:
            self.client = None
            self.model = None
            
        # NLLB model removed as we use LAfricaMobile
        # self._nllb_model = None
        # self._nllb_tokenizer = None
        # self._nllb_device = "cpu"
        
        # LAfricaMobile Service (lazy loaded)
        self._lafricamobile_service = None

    def _get_lafricamobile_service(self):
        if self._lafricamobile_service is None:
            from app.services.lafricamobile import LAfricaMobileService
            self._lafricamobile_service = LAfricaMobileService()
        return self._lafricamobile_service

    # NLLB loading method removed
    # def _load_nllb_model(self):
    #     ...

    def _parse_history(self, history_str: str) -> List[Dict[str, str]]:
        """
        Parse the string history into OpenAI message format.
        History is expected to be in format:
        User: ...
        Assistant: ...
        System (Tool Output): ...
        """
        messages = []
        lines = history_str.strip().split('\n')
        
        current_role = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("User:"):
                if current_role:
                    messages.append({"role": current_role, "content": " ".join(current_content)})
                current_role = "user"
                current_content = [line.replace("User:", "").strip()]
            elif line.startswith("Assistant:"):
                if current_role:
                    messages.append({"role": current_role, "content": " ".join(current_content)})
                current_role = "assistant"
                current_content = [line.replace("Assistant:", "").strip()]
            elif line.startswith("System (Tool Output"):
                if current_role:
                    messages.append({"role": current_role, "content": " ".join(current_content)})
                
                # Extract content removing the prefix
                content = line.split("):", 1)[1].strip() if "):" in line else line
                
                current_role = "system" 
                current_content = ["Tool output from previous turn: " + content]
            else:
                if current_role:
                    current_content.append(line)
        
        if current_role:
            messages.append({"role": current_role, "content": " ".join(current_content)})
            
        return messages

    async def generate_response_with_tools(
        self, 
        system_instruction: str, 
        context: str, 
        history: str, 
        user_message: str
    ) -> Dict[str, Any]:
        """
        Generate response with potential function calls for appointment booking.
        Returns a dict with:
        - 'type': 'text' or 'function_call'
        - 'content': text response or function call details
        """
        if not self.client:
            return {"type": "text", "content": "OpenAI API Key not configured. Mock response."}
        
        messages = [
            {"role": "system", "content": f"{system_instruction}\n\nContext from Knowledge Base:\n{context}"}
        ]
        
        # Add history
        # Note: In a real production system, we should store structured messages in DB
        # instead of parsing a string history. This is an adaptation layer.
        parsed_history = self._parse_history(history)
        messages.extend(parsed_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=APPOINTMENT_TOOLS,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check for tool calls
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                return {
                    "type": "function_call",
                    "content": {
                        "name": tool_call.function.name,
                        "args": json.loads(tool_call.function.arguments)
                    }
                }
            
            return {"type": "text", "content": message.content or "Je n'ai pas compris."}
            
        except Exception as e:
            return {"type": "text", "content": f"Error generating response: {str(e)}"}

    async def continue_with_function_result(
        self,
        system_instruction: str,
        function_name: str,
        function_result: str
    ) -> Dict[str, Any]:
        """
        Continue the conversation after executing a function call.
        """
        if not self.client:
            return {"type": "text", "content": "OpenAI API Key not configured."}
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "system", "content": f"System (Tool '{function_name}' Output): {function_result}"},
            {"role": "user", "content": "Continue la conversation en te basant sur ce résultat. Si c'est une liste de créneaux, propose-les clairement."}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            message = response.choices[0].message
             
            # Check for MORE tool calls (nested)
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                return {
                    "type": "function_call",
                    "content": {
                        "name": tool_call.function.name,
                        "args": json.loads(tool_call.function.arguments)
                    }
                }
            
            return {"type": "text", "content": message.content}
            
        except Exception as e:
            return {"type": "text", "content": f"Error: {str(e)}"}

    async def translate_wolof_to_french(self, text: str) -> str:
        """Translate Wolof text to French using LAfricaMobile."""
        # Try LAfricaMobile
        try:
            print("[Translation] Translating Wolof -> French via LAfricaMobile...")
            service = self._get_lafricamobile_service()
            return await service.translate(text, to_lang="french")
        except Exception as e:
            print(f"[Translation] LAfricaMobile failed ({e}). Returning original text.")
            # raise e # Or return text? For now return text to avoid crash
            return text

        # GPT Fallback REMOVED to ensure strict usage of LAfricaMobile
        # if not self.client: ...

    async def translate_french_to_wolof(self, text: str) -> str:
        """Translate French text to Wolof using LAfricaMobile."""
        # Try LAfricaMobile
        try:
            print("[Translation] Translating French -> Wolof via LAfricaMobile...")
            service = self._get_lafricamobile_service()
            return await service.translate(text, to_lang="wolof")
        except Exception as e:
            print(f"[Translation] LAfricaMobile failed ({e}). Returning original text.")
            return text

        # NLLB and GPT Fallback REMOVED to ensure strict usage of LAfricaMobile

    async def detect_language(self, text: str) -> str:
        """
        Detect the language of the given text using GPT.
        Returns ISO language code: 'wo' for Wolof, 'fr' for French, etc.
        """
        if not self.client or not text.strip():
            return "fr"  # Default to French
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Tu es un detecteur de langue expert. Identifie la langue du texte suivant.
Reponds UNIQUEMENT avec le code ISO de la langue:
- 'wo' pour Wolof
- 'fr' pour Francais
- 'en' pour Anglais
- 'ar' pour Arabe

Reponds seulement avec le code, rien d'autre."""
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0,
                max_tokens=5
            )
            detected = response.choices[0].message.content.strip().lower()
            # Clean up response
            if detected in ['wo', 'wolof']:
                return 'wo'
            elif detected in ['fr', 'french', 'francais', 'français']:
                return 'fr'
            elif detected in ['en', 'english', 'anglais']:
                return 'en'
            elif detected in ['ar', 'arabic', 'arabe']:
                return 'ar'
            else:
                return 'fr'  # Default
        except Exception as e:
            print(f"[Language] Detection failed: {e}")
            return "fr"
