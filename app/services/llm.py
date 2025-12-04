import google.generativeai as genai
from app.core.config import settings

class LLMService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    async def generate_response(self, system_instruction: str, context: str, history: str, user_message: str) -> str:
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
