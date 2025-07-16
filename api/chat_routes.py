from flask import Blueprint, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time
import logging
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from services.openai_service import OpenAIService
from services.context_service import ContextService
from services.financial_data_service import FinancialDataService
from services.cache_service import CacheService
from utils.rate_limiter import RateLimiter
from utils.validators import validate_message_input, validate_session_id
from app import redis_client

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

# Initialize services
openai_service = OpenAIService()
context_service = ContextService()
financial_data_service = FinancialDataService()
cache_service = CacheService(redis_client)
rate_limiter = RateLimiter(redis_client)

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=10)

@chat_bp.route('/chat/message', methods=['POST'])
def send_message():
    """Send a message to the AI assistant"""
    try:
        # Validate input
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        validation_result = validate_message_input(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
        
        user_message = data['message']
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'No session found'}), 400
        
        # Check rate limits
        user_tier = session.get('user_tier', 1)
        if not rate_limiter.check_rate_limit(session_id, user_tier):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Check daily message limits
        if not rate_limiter.check_daily_limit(session_id, user_tier):
            tier_limits = {1: 10, 2: 50, 3: 100, 4: 200, 5: 500, 6: 1000, 7: -1}
            limit = tier_limits.get(user_tier, 10)
            message = f"Daily message limit reached ({limit} messages). Please upgrade your tier for more messages."
            return jsonify({'error': message}), 429
        
        # Check for cached response
        cached_response = cache_service.get_cached_response(session_id, user_message)
        if cached_response:
            logger.info(f"Returning cached response for session {session_id}")
            return jsonify({
                'response': cached_response,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
        
        start_time = time.time()
        
        # Get or create session
        chat_session = context_service.create_or_update_session(session_id, user_tier)
        if not chat_session:
            return jsonify({'error': 'Failed to create session'}), 500
        
        # Get session context
        context = context_service.get_session_context(session_id)
        
        # Extract context from current message
        message_context = context_service.extract_context_from_message(user_message)
        context.update(message_context)
        
        # Classify user intent
        def classify_intent():
            return asyncio.run(openai_service.classify_user_intent(user_message))
        
        intent_result = executor.submit(classify_intent).result(timeout=10)
        
        # Route to appropriate handler based on intent
        ai_response = None
        context_used = {}
        
        if intent_result['intent'] == 'market_data':
            # Get market data and interpret
            market_data = financial_data_service.get_market_overview()
            if market_data['success']:
                def get_market_interpretation():
                    return asyncio.run(openai_service.get_market_interpretation(
                        market_data['data'], user_message, context
                    ))
                
                response_result = executor.submit(get_market_interpretation).result(timeout=15)
                ai_response = response_result['response']
                context_used = {'market_data': market_data['data'], 'intent': intent_result}
        
        elif intent_result['intent'] == 'portfolio_analysis':
            # Get portfolio data from context
            portfolio_data = context.get('user_context', {}).get('portfolio_data', {})
            if not portfolio_data:
                # Generate mock portfolio for demonstration
                portfolio_data = financial_data_service.get_portfolio_analysis({})['data']
            
            def analyze_portfolio():
                return asyncio.run(openai_service.analyze_portfolio_question(
                    user_message, portfolio_data, context
                ))
            
            response_result = executor.submit(analyze_portfolio).result(timeout=15)
            ai_response = response_result['response']
            context_used = {'portfolio_data': portfolio_data, 'intent': intent_result}
        
        elif intent_result['intent'] == 'educational':
            # Get user's learning level
            learning_progress = context_service.get_user_learning_progress(session_id)
            user_level = learning_progress.get('level', 'beginner')
            
            # Extract topic from message
            topic = user_message  # Simplified - in production, extract specific topic
            
            def get_educational_response():
                return asyncio.run(openai_service.generate_educational_response(
                    topic, user_level, context
                ))
            
            response_result = executor.submit(get_educational_response).result(timeout=15)
            ai_response = response_result['response']
            context_used = {'learning_level': user_level, 'topic': topic, 'intent': intent_result}
        
        else:
            # General financial query
            def get_financial_response():
                return asyncio.run(openai_service.process_financial_query(user_message, context))
            
            response_result = executor.submit(get_financial_response).result(timeout=15)
            ai_response = response_result['response']
            context_used = {'intent': intent_result}
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Save message to database
        saved_message = context_service.save_message(
            session_id, user_message, ai_response, context_used, response_time_ms
        )
        
        if not saved_message:
            logger.error("Failed to save message to database")
        
        # Cache the response
        cache_service.cache_response(session_id, user_message, ai_response)
        
        # Update rate limiter
        rate_limiter.increment_usage(session_id)
        
        return jsonify({
            'response': ai_response,
            'response_time_ms': response_time_ms,
            'intent': intent_result['intent'],
            'context_used': bool(context_used),
            'timestamp': datetime.now().isoformat(),
            'cached': False
        })
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({'error': 'An error occurred while processing your message'}), 500

@chat_bp.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        # Validate session ID
        if not validate_session_id(session_id):
            return jsonify({'error': 'Invalid session ID'}), 400
        
        # Check if user owns this session
        if session.get('session_id') != session_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Cap at 100 messages
        
        history = context_service.get_conversation_history(session_id, limit)
        
        return jsonify({
            'history': history,
            'session_id': session_id,
            'total_messages': len(history)
        })
    
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({'error': 'Failed to retrieve chat history'}), 500

@chat_bp.route('/chat/context/update', methods=['POST'])
def update_context():
    """Update user context"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 400
        
        success = context_service.update_user_context(session_id, data)
        
        if success:
            return jsonify({'message': 'Context updated successfully'})
        else:
            return jsonify({'error': 'Failed to update context'}), 500
    
    except Exception as e:
        logger.error(f"Error updating context: {e}")
        return jsonify({'error': 'Failed to update context'}), 500

@chat_bp.route('/chat/suggestions', methods=['GET'])
def get_suggestions():
    """Get conversation suggestions based on user tier and context"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 400
        
        user_tier = session.get('user_tier', 1)
        
        # Get basic suggestions based on tier
        suggestions = {
            1: [  # Freemium
                "What is a stock?",
                "Explain market volatility",
                "How do I start investing?",
                "What are the major stock indices?"
            ],
            2: [  # Market Hours Pro
                "Analyze my portfolio performance",
                "What's happening in the market today?",
                "Explain dividend investing",
                "How do I diversify my portfolio?"
            ],
            3: [  # Higher tiers
                "Provide advanced market analysis",
                "Create a custom investment strategy",
                "Analyze sector performance trends",
                "Explain options trading strategies"
            ]
        }
        
        # Get suggestions for user tier (default to tier 1)
        tier_suggestions = suggestions.get(user_tier, suggestions[1])
        if user_tier >= 3:
            tier_suggestions = suggestions[3]
        
        return jsonify({
            'suggestions': tier_suggestions,
            'user_tier': user_tier,
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return jsonify({'error': 'Failed to get suggestions'}), 500

@chat_bp.route('/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history for current session"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 400
        
        # Clear cache
        cache_service.clear_session_cache(session_id)
        
        # Note: In production, you might want to soft-delete messages
        # rather than hard delete for audit purposes
        
        return jsonify({'message': 'Chat history cleared successfully'})
    
    except Exception as e:
        logger.error(f"Error clearing chat: {e}")
        return jsonify({'error': 'Failed to clear chat history'}), 500

@chat_bp.route('/chat/status', methods=['GET'])
def get_chat_status():
    """Get current chat session status"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session found'}), 400
        
        user_tier = session.get('user_tier', 1)
        
        # Get usage statistics
        usage_stats = rate_limiter.get_usage_stats(session_id)
        
        return jsonify({
            'session_id': session_id,
            'user_tier': user_tier,
            'usage_stats': usage_stats,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting chat status: {e}")
        return jsonify({'error': 'Failed to get chat status'}), 500
