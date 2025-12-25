import structlog
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from wellsync_ai.utils.llm_config import LLMConfig

logger = structlog.get_logger()

class GoogleGeminiChat:
    """
    Wrapper for Google Gemini Chat API.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        if genai and self.config.api_key:
            try:
                genai.configure(api_key=self.config.api_key)
                self.model = genai.GenerativeModel('gemini-3-flash-preview')
                logger.info("Gemini Model configured successfully")
            except Exception as e:
                self.model = None
                logger.error(f"Gemini configuration failed: {e}")
        else:
             self.model = None
             reason = "genai lib missing" if not genai else "API Key missing"
             logger.warning(f"Gemini API not configured: {reason}")
             
    def generate_response(self, message: str, context: str = "") -> str:
        """
        Generate a response from the LLM.
        """
        if not self.model:
            return "I am unable to process your request at the moment (LLM not configured)."
            
        try:
            # System Prompt for Wellness Coach
            system_prompt = """You are the WellSync AI Wellness Coach. 
Your goal is to help users improve their health through holistic plans covering fitness, nutrition, sleep, and mental wellness.
You are supportive, knowledgeable, data-driven, and concise. 
Always answer in the context of the user's wellness journey.
Do not offer generic AI assistance (like writing essays or coding) unless it relates to the health app.
If you don't know something, suggest the user consult a professional healthcare provider."""

            # Construct prompt with context
            context_str = str(context) if context else ""
            prompt = f"{system_prompt}\n\nContext: {context_str}\n\nUser: {message}\nAI:"
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error("LLM Generation Failed", error=str(e))
            return "I'm having trouble thinking right now. Please try again later."
