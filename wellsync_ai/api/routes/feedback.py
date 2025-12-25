from flask import Blueprint, jsonify, g
from datetime import datetime
import structlog
from typing import Dict, Any

from wellsync_ai.api.utils import validate_json_request, WellnessAPIError
from wellsync_ai.data.database import get_database_manager

logger = structlog.get_logger()
feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback', methods=['POST'])
@validate_json_request(required_fields=['user_id', 'accepted'])
def submit_feedback(request_data: Dict[str, Any]):
    """
    Submit User Feedback for Generated Plan
    ---
    tags:
      - Feedback
    summary: Store user feedback (accept/reject) for a plan
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - accepted
          properties:
            user_id:
              type: string
            accepted:
              type: boolean
            plan_id:
              type: string
            reason:
              type: string
            state_id:
              type: string
              description: Optional state ID (e.g., plan generation session ID)
    responses:
      200:
        description: Feedback stored successfully
      500:
        description: Failed to store feedback
    """
    try:
        user_id = request_data['user_id']
        accepted = request_data['accepted']
        
        logger.info(
            "Feedback request received", 
            user_id=user_id,
            accepted=accepted,
            request_id=g.request_id
        )
        
        db_manager = get_database_manager()
        
        # Prepare feedback data
        feedback_payload = {
            'accepted': accepted,
            'plan_id': request_data.get('plan_id'),
            'reason': request_data.get('reason'),
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Determine state_id (default to 'plan_feedback' if not provided)
        state_id = request_data.get('state_id', 'plan_feedback')
        
        # Store feedback
        feedback_id = db_manager.store_user_feedback(
            state_id=state_id,
            feedback=feedback_payload,
            request_id=g.request_id
        )
        
        return jsonify({
            'success': True,
            'feedback_id': feedback_id,
            'timestamp': datetime.now().isoformat(),
            'request_id': g.request_id
        }), 200

    except Exception as e:
        logger.error("Feedback endpoint failed", error=str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
