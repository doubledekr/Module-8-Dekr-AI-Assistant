import logging
from typing import Dict, Any, List
from models import ChatSession, ChatMessage, UserContext
from app import db
from datetime import datetime, timedelta

class ContextService:
    """Service for managing user context and conversation history"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive context for a session"""
        try:
            session = ChatSession.query.filter_by(id=session_id).first()
            if not session:
                return {}
            
            # Get recent messages for conversation context
            recent_messages = ChatMessage.query.filter_by(
                session_id=session_id
            ).order_by(ChatMessage.timestamp.desc()).limit(5).all()
            
            # Get user context
            user_context = UserContext.query.filter_by(session_id=session_id).first()
            
            context = {
                "session_info": session.to_dict(),
                "recent_messages": [msg.to_dict() for msg in reversed(recent_messages)],
                "user_context": user_context.to_dict() if user_context else {},
                "conversation_length": len(recent_messages),
                "session_duration": (datetime.utcnow() - session.created_at).total_seconds() / 3600  # in hours
            }
            
            return context
        except Exception as e:
            self.logger.error(f"Error getting session context: {e}")
            return {}
    
    def update_user_context(self, session_id: str, context_updates: Dict[str, Any]) -> bool:
        """Update user context with new information"""
        try:
            user_context = UserContext.query.filter_by(session_id=session_id).first()
            
            if not user_context:
                user_context = UserContext(session_id=session_id)
                db.session.add(user_context)
            
            # Update various context fields
            if 'preferences' in context_updates:
                user_context.user_preferences.update(context_updates['preferences'])
            
            if 'portfolio_data' in context_updates:
                user_context.portfolio_data.update(context_updates['portfolio_data'])
            
            if 'recent_activity' in context_updates:
                user_context.recent_activity.update(context_updates['recent_activity'])
            
            if 'learning_progress' in context_updates:
                user_context.learning_progress.update(context_updates['learning_progress'])
            
            user_context.updated_at = datetime.utcnow()
            db.session.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating user context: {e}")
            db.session.rollback()
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        try:
            messages = ChatMessage.query.filter_by(
                session_id=session_id
            ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
            
            return [msg.to_dict() for msg in reversed(messages)]
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
    
    def create_or_update_session(self, session_id: str, user_tier: int = 1, session_type: str = 'general') -> ChatSession:
        """Create or update a chat session"""
        try:
            session = ChatSession.query.filter_by(id=session_id).first()
            
            if not session:
                session = ChatSession(
                    id=session_id,
                    user_tier=user_tier,
                    session_type=session_type,
                    context_data={}
                )
                db.session.add(session)
            else:
                session.updated_at = datetime.utcnow()
                session.user_tier = user_tier
                session.session_type = session_type
            
            db.session.commit()
            return session
        except Exception as e:
            self.logger.error(f"Error creating/updating session: {e}")
            db.session.rollback()
            return None
    
    def save_message(self, session_id: str, user_message: str, ai_response: str, context_used: Dict[str, Any] = None, response_time_ms: int = 0) -> ChatMessage:
        """Save a chat message to the database"""
        try:
            message = ChatMessage(
                session_id=session_id,
                user_message=user_message,
                ai_response=ai_response,
                context_used=context_used or {},
                response_time_ms=response_time_ms
            )
            
            db.session.add(message)
            db.session.commit()
            
            return message
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            db.session.rollback()
            return None
    
    def get_user_learning_progress(self, session_id: str) -> Dict[str, Any]:
        """Get user's learning progress and preferences"""
        try:
            user_context = UserContext.query.filter_by(session_id=session_id).first()
            
            if not user_context:
                return {
                    "level": "beginner",
                    "topics_covered": [],
                    "preferred_learning_style": "conversational",
                    "areas_of_interest": []
                }
            
            return user_context.learning_progress
        except Exception as e:
            self.logger.error(f"Error getting learning progress: {e}")
            return {}
    
    def extract_context_from_message(self, user_message: str) -> Dict[str, Any]:
        """Extract contextual information from user message"""
        context = {}
        
        # Simple keyword-based context extraction
        message_lower = user_message.lower()
        
        # Detect mentioned financial instruments
        financial_keywords = {
            'stocks': ['stock', 'equity', 'share', 'ticker'],
            'crypto': ['bitcoin', 'ethereum', 'crypto', 'blockchain'],
            'bonds': ['bond', 'treasury', 'yield'],
            'options': ['option', 'call', 'put', 'strike'],
            'forex': ['forex', 'currency', 'exchange rate']
        }
        
        mentioned_instruments = []
        for instrument, keywords in financial_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                mentioned_instruments.append(instrument)
        
        if mentioned_instruments:
            context['mentioned_instruments'] = mentioned_instruments
        
        # Detect intent indicators
        intent_keywords = {
            'learning': ['learn', 'explain', 'understand', 'what is', 'how does'],
            'analysis': ['analyze', 'evaluate', 'assess', 'opinion'],
            'strategy': ['strategy', 'plan', 'approach', 'method'],
            'current_market': ['current', 'today', 'now', 'latest']
        }
        
        detected_intents = []
        for intent, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        if detected_intents:
            context['detected_intents'] = detected_intents
        
        return context
