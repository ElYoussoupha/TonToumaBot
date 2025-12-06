import json
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from app.core.config import settings


# Define appointment-related function declarations
APPOINTMENT_FUNCTIONS = [
    FunctionDeclaration(
        name="search_doctors",
        description="Recherche des médecins disponibles par spécialité. Utilisez cette fonction quand l'utilisateur veut prendre un rendez-vous et mentionne une spécialité ou demande les médecins disponibles.",
        parameters={
            "type": "object",
            "properties": {
                "specialty": {
                    "type": "string",
                    "description": "Nom de la spécialité médicale recherchée (ex: cardiologie, pédiatrie, dermatologie)"
                }
            },
            "required": []
        }
    ),
    FunctionDeclaration(
        name="get_available_slots",
        description="Obtient les créneaux de rendez-vous disponibles pour un médecin ou une spécialité à une date donnée.",
        parameters={
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
            "required": ["date"]
        }
    ),
    FunctionDeclaration(
        name="book_appointment",
        description="Réserve un rendez-vous pour le patient. Utilisez cette fonction uniquement quand vous avez toutes les informations nécessaires: médecin, date, heure, nom du patient, email et motif.",
        parameters={
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
    )
]


class LLMService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Model without tools for regular chat
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            # Model with appointment tools
            self.model_with_tools = genai.GenerativeModel(
                'gemini-2.0-flash',
                tools=[Tool(function_declarations=APPOINTMENT_FUNCTIONS)]
            )
        else:
            self.model = None
            self.model_with_tools = None

    async def generate_response(self, system_instruction: str, context: str, history: str, user_message: str) -> str:
        """Original method for regular chat responses"""
        if not self.model:
            return "Gemini API Key not configured. Mock response."
        
        prompt = f"""
        System: {system_instruction}
        Context: {context}
        History: {history}
        User: {user_message}
        Assistant:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

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
        if not self.model_with_tools:
            return {"type": "text", "content": "Gemini API Key not configured. Mock response."}
        
        prompt = f"""
        System: {system_instruction}
        
        Tu es un assistant capable de prendre des rendez-vous médicaux. Quand l'utilisateur souhaite prendre un rendez-vous:
        1. Demande quelle spécialité ou quel médecin il recherche
        2. Demande la date souhaitée
        3. Propose les créneaux disponibles
        4. Collecte les informations du patient (nom, email, motif)
        5. Confirme le rendez-vous
        
        Utilise les fonctions disponibles pour rechercher les médecins, obtenir les créneaux et réserver.
        
        Context: {context}
        History: {history}
        User: {user_message}
        """
        
        try:
            response = self.model_with_tools.generate_content(prompt)
            
            # Check if response contains function calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        return {
                            "type": "function_call",
                            "content": {
                                "name": fc.name,
                                "args": dict(fc.args) if fc.args else {}
                            }
                        }
                    elif hasattr(part, 'text') and part.text:
                        return {"type": "text", "content": part.text}
            
            # Fallback to text response
            return {"type": "text", "content": response.text if hasattr(response, 'text') else "Je n'ai pas compris votre demande."}
            
        except Exception as e:
            return {"type": "text", "content": f"Error generating response: {str(e)}"}

    async def continue_with_function_result(
        self,
        original_prompt: str,
        function_name: str,
        function_result: str
    ) -> Dict[str, Any]:
        """
        Continue the conversation after executing a function call.
        """
        if not self.model_with_tools:
            return {"type": "text", "content": "Gemini API Key not configured."}
        
        # Format the function result for the model
        continuation_prompt = f"""
        {original_prompt}
        
        La fonction {function_name} a retourné le résultat suivant:
        {function_result}
        
        Utilise ce résultat pour continuer la conversation avec l'utilisateur. 
        Si c'est une liste de médecins ou de créneaux, présente-les de manière claire.
        Si c'est une confirmation de rendez-vous, informe l'utilisateur du succès.
        """
        
        try:
            response = self.model_with_tools.generate_content(continuation_prompt)
            
            # Check for more function calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        return {
                            "type": "function_call",
                            "content": {
                                "name": fc.name,
                                "args": dict(fc.args) if fc.args else {}
                            }
                        }
                    elif hasattr(part, 'text') and part.text:
                        return {"type": "text", "content": part.text}
            
            return {"type": "text", "content": response.text if hasattr(response, 'text') else "Voici ce que j'ai trouvé."}
            
        except Exception as e:
            return {"type": "text", "content": f"Error: {str(e)}"}
