import re
from typing import Dict, Any, List

def validate_message_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate chat message input"""
    
    if not isinstance(data, dict):
        return {'valid': False, 'error': 'Invalid data format'}
    
    if 'message' not in data:
        return {'valid': False, 'error': 'Message field is required'}
    
    message = data['message']
    
    # Check message type
    if not isinstance(message, str):
        return {'valid': False, 'error': 'Message must be a string'}
    
    # Check message length
    if len(message.strip()) == 0:
        return {'valid': False, 'error': 'Message cannot be empty'}
    
    if len(message) > 5000:
        return {'valid': False, 'error': 'Message too long (max 5000 characters)'}
    
    # Check for potentially harmful content
    if contains_harmful_content(message):
        return {'valid': False, 'error': 'Message contains inappropriate content'}
    
    return {'valid': True, 'message': message.strip()}

def validate_session_id(session_id: str) -> bool:
    """Validate session ID format"""
    if not isinstance(session_id, str):
        return False
    
    # Check UUID format
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, session_id))

def validate_context_update(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate context update data"""
    
    if not isinstance(data, dict):
        return {'valid': False, 'error': 'Invalid data format'}
    
    allowed_fields = ['preferences', 'portfolio_data', 'recent_activity', 'learning_progress']
    
    for field in data:
        if field not in allowed_fields:
            return {'valid': False, 'error': f'Invalid field: {field}'}
    
    # Validate preferences
    if 'preferences' in data:
        if not isinstance(data['preferences'], dict):
            return {'valid': False, 'error': 'Preferences must be a dictionary'}
    
    # Validate portfolio_data
    if 'portfolio_data' in data:
        if not isinstance(data['portfolio_data'], dict):
            return {'valid': False, 'error': 'Portfolio data must be a dictionary'}
    
    # Validate recent_activity
    if 'recent_activity' in data:
        if not isinstance(data['recent_activity'], dict):
            return {'valid': False, 'error': 'Recent activity must be a dictionary'}
    
    # Validate learning_progress
    if 'learning_progress' in data:
        if not isinstance(data['learning_progress'], dict):
            return {'valid': False, 'error': 'Learning progress must be a dictionary'}
    
    return {'valid': True}

def validate_financial_symbol(symbol: str) -> bool:
    """Validate financial symbol format"""
    if not isinstance(symbol, str):
        return False
    
    # Basic symbol validation (1-5 uppercase letters)
    pattern = r'^[A-Z]{1,5}$'
    return bool(re.match(pattern, symbol.upper()))

def validate_user_tier(tier: int) -> bool:
    """Validate user tier"""
    return isinstance(tier, int) and 1 <= tier <= 7

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not isinstance(text, str):
        return ""
    
    # Remove potentially harmful characters
    # This is a basic implementation - in production, use a proper sanitization library
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    sanitized = sanitized[:5000]
    
    return sanitized.strip()

def contains_harmful_content(text: str) -> bool:
    """Check for potentially harmful content"""
    if not isinstance(text, str):
        return False
    
    # Simple harmful content detection
    # In production, use a proper content moderation service
    harmful_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'document\.',
        r'window\.',
    ]
    
    text_lower = text.lower()
    
    for pattern in harmful_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False

def validate_portfolio_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate portfolio data structure"""
    
    if not isinstance(data, dict):
        return {'valid': False, 'error': 'Portfolio data must be a dictionary'}
    
    # Check required fields
    required_fields = ['positions', 'total_value']
    for field in required_fields:
        if field not in data:
            return {'valid': False, 'error': f'Missing required field: {field}'}
    
    # Validate positions
    if 'positions' in data:
        positions = data['positions']
        if not isinstance(positions, list):
            return {'valid': False, 'error': 'Positions must be a list'}
        
        for position in positions:
            if not isinstance(position, dict):
                return {'valid': False, 'error': 'Each position must be a dictionary'}
            
            required_position_fields = ['symbol', 'quantity', 'price']
            for field in required_position_fields:
                if field not in position:
                    return {'valid': False, 'error': f'Missing position field: {field}'}
    
    # Validate total_value
    if 'total_value' in data:
        total_value = data['total_value']
        if not isinstance(total_value, (int, float)) or total_value < 0:
            return {'valid': False, 'error': 'Total value must be a non-negative number'}
    
    return {'valid': True}

def validate_news_query(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate news query parameters"""
    
    if not isinstance(params, dict):
        return {'valid': False, 'error': 'Parameters must be a dictionary'}
    
    # Validate limit
    if 'limit' in params:
        limit = params['limit']
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            return {'valid': False, 'error': 'Limit must be between 1 and 100'}
    
    # Validate symbols
    if 'symbols' in params:
        symbols = params['symbols']
        if not isinstance(symbols, list):
            return {'valid': False, 'error': 'Symbols must be a list'}
        
        for symbol in symbols:
            if not validate_financial_symbol(symbol):
                return {'valid': False, 'error': f'Invalid symbol format: {symbol}'}
    
    return {'valid': True}
