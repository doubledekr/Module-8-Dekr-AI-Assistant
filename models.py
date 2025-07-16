from app import db
from sqlalchemy import String, Text, Integer, DateTime, JSON
from datetime import datetime
import uuid

class ChatSession(db.Model):
    """Chat session model"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(String(36), nullable=True)  # Can be null for anonymous sessions
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    context_data = db.Column(JSON, default=dict)
    session_type = db.Column(String(50), default='general')
    user_tier = db.Column(Integer, default=1)
    
    # Relationship to messages
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'context_data': self.context_data,
            'session_type': self.session_type,
            'user_tier': self.user_tier
        }

class ChatMessage(db.Model):
    """Chat message model"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    user_message = db.Column(Text, nullable=False)
    ai_response = db.Column(Text, nullable=False)
    timestamp = db.Column(DateTime, default=datetime.utcnow)
    context_used = db.Column(JSON, default=dict)
    response_time_ms = db.Column(Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'timestamp': self.timestamp.isoformat(),
            'context_used': self.context_used,
            'response_time_ms': self.response_time_ms
        }

class UserContext(db.Model):
    """User context model for storing user preferences and state"""
    __tablename__ = 'user_contexts'
    
    id = db.Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    user_preferences = db.Column(JSON, default=dict)
    portfolio_data = db.Column(JSON, default=dict)
    recent_activity = db.Column(JSON, default=dict)
    learning_progress = db.Column(JSON, default=dict)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_preferences': self.user_preferences,
            'portfolio_data': self.portfolio_data,
            'recent_activity': self.recent_activity,
            'learning_progress': self.learning_progress,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
