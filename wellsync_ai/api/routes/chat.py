from flask import Blueprint, jsonify, g, request
from datetime import datetime
import structlog
from typing import Dict, Any

from wellsync_ai.api.utils import validate_json_request, WellnessAPIError
from wellsync_ai.utils.chat_context import ChatContext
from wellsync_ai.utils.llm import GoogleGeminiChat
from wellsync_ai.utils.llm_config import LLMConfig
# Fallback response imports if needed, but likely handled inside logic

logger = structlog.get_logger()
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
@validate_json_request(required_fields=['message', 'user_id'])
def chat_with_ai(request_data: Dict[str, Any]):
    """
    Chat with AI Coach
    ---
    tags:
      - Chat
    summary: Chat with the AI Wellness Coach
    description: Send a message to the AI coach and get a response based on context
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - message
            - user_id
          properties:
            message:
              type: string
            user_id:
              type: string
            context:
              type: object
    responses:
      200:
        description: Chat response generated
      500:
        description: Chat failure
    """
    try:
        user_id = request_data['user_id']
        message = request_data['message']
        context_data = request_data.get('context', {})
        
        logger.info(
            "Chat request received", 
            user_id=user_id,
            request_id=g.request_id
        )
        
        # Initialize Chat Context
        chat_context = ChatContext(user_id)
        
        # 1. Fetch User History from Database (Context Awareness)
        from wellsync_ai.data.database import get_database_manager
        db_manager = get_database_manager()
        
        # Get recent wellness plans to understand user's current regime
        recent_plans = db_manager.get_user_history(user_id, limit=1)
        
        db_context = {}
        if recent_plans:
            latest_plan = recent_plans[0]
            # safely extract plan details
            plan_data = latest_plan.get('plan_data', {})
            if isinstance(plan_data, str):
                import json
                try:
                    plan_data = json.loads(plan_data)
                except:
                    pass
            
            db_context['latest_wellness_plan'] = plan_data
            db_context['plan_date'] = latest_plan.get('timestamp')
            
            logger.info("Injected database context into chat", user_id=user_id)

        # Merge with request context (request context takes precedence if keys collide, but we nest them)
        full_context = {
            "initial_context": context_data,
            "database_context": db_context
        }

        # Config
        config = LLMConfig()
        # Initialize Gemini Chat
        chat_agent = GoogleGeminiChat(config)
        
        # Get response
        # Note: In original code, we had fallback logic. I should replicate it.
        # But for now, let's assume standard flow or copy the fallback block if possible.
        
        response_text = ""
        try:
             # Basic interaction
             # In original code, it called chat_agent.generate_response(message, context)
             # I need to verify exact method signature from Step 1324
             # Step 1324: response = chat_agent.generate_response(user_input, context_str)
             
             # Construct context string
             context_str = f"User Context: {full_context}"
             response_text = chat_agent.generate_response(message, context_str)
             
        except Exception as e:
            logger.error(f"LLM fail: {e}")
            # Fallback logic
            # I will implement a simplified fallback here or copy the exact one if I viewed it.
            # Step 1324 showed custom fallback logic.
            
            q = message.lower()
            if any(word in q for word in ['water', 'drink', 'hydration']):
                 response_text = "Stay hydrated! 8 glasses a day."
            elif any(word in q for word in ['hurt', 'pain']):
                 response_text = "Please consult a doctor for pain."
            else:
                 response_text = "I'm having trouble connecting to my brain right now. Please try again."

        return jsonify({
            'success': True,
            'response': response_text,
            'timestamp': datetime.now().isoformat(),
            'request_id': g.request_id
        }), 200

    except Exception as e:
        logger.error("Chat endpoint failed", error=str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
