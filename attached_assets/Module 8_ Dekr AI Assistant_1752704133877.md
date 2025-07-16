# Module 8: Dekr AI Assistant

## Overview
The Dekr AI Assistant provides intelligent conversational support for users, helping them understand market data, navigate the platform, learn financial concepts, and get personalized insights. This module integrates ChatGPT with financial expertise and user context awareness.

## Core Features

### 1. Contextual Financial Assistant
- Real-time market data interpretation
- Portfolio analysis and insights
- Strategy explanation and guidance
- Educational content delivery

### 2. User Context Awareness
- Access to user preferences and tier
- Portfolio and deck information
- Recent activity and behavior patterns
- Personalized response adaptation

### 3. Multi-Modal Support
- Text-based conversations
- Voice input/output capabilities
- Chart and data visualization explanations
- Educational content recommendations

## Technical Architecture

### API Endpoints
```
POST /api/v1/chat/message
GET /api/v1/chat/history/{user_id}
POST /api/v1/chat/context/update
GET /api/v1/chat/suggestions
POST /api/v1/chat/voice/input
GET /api/v1/chat/voice/output/{message_id}
```

### Database Schema
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    context_data JSONB,
    session_type VARCHAR(50)
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id),
    user_message TEXT,
    ai_response TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    context_used JSONB,
    response_time_ms INTEGER
);
```

## Replit Implementation Prompt

Create a new Replit project called "dekr-ai-assistant" with the following structure:

```
dekr-ai-assistant/
├── main.py
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── context.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py
│   │   ├── context_service.py
│   │   └── voice_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── voice.py
│   └── utils/
│       ├── __init__.py
│       ├── prompts.py
│       └── validators.py
├── tests/
│   ├── __init__.py
│   ├── test_chat.py
│   └── test_context.py
└── README.md
```

### Environment Variables
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
DATABASE_URL=postgresql://user:pass@localhost/dekr
REDIS_URL=redis://localhost:6379
POLYGON_API_KEY=your_polygon_key
MARKETAUX_API_KEY=your_marketaux_key
```

### Key Implementation Requirements

1. **OpenAI Integration**: Use GPT-4 with financial expertise prompts
2. **Context Management**: Maintain user context across conversations
3. **Real-time Data**: Access live market data for current insights
4. **Educational Integration**: Connect with education module content
5. **Voice Support**: Text-to-speech and speech-to-text capabilities
6. **Response Caching**: Cache common responses for performance
7. **Rate Limiting**: Implement tier-based usage limits
8. **Analytics**: Track conversation patterns and user satisfaction

### Core Functions to Implement

```python
async def process_user_message(user_id: str, message: str, context: dict)
async def get_financial_context(user_id: str, symbols: list)
async def generate_educational_response(topic: str, user_level: str)
async def analyze_portfolio_question(user_id: str, question: str)
async def provide_strategy_guidance(strategy_id: str, user_question: str)
```

### Testing Requirements
- Unit tests for all core functions
- Integration tests with OpenAI API
- Context persistence testing
- Performance benchmarks
- Voice functionality testing

## Integration Points

### With Other Modules
- **User Preference Engine**: Access user preferences and behavior
- **Polygon Data Service**: Real-time market data for context
- **Strategy Builder**: Explain strategies and provide guidance
- **Education Module**: Deliver personalized learning content
- **User Deck Manager**: Analyze user portfolios and decks

### External Services
- **OpenAI GPT-4**: Core conversational AI
- **Polygon.io**: Real-time market data
- **MarketAux**: News and sentiment data
- **Text-to-Speech Service**: Voice output
- **Speech-to-Text Service**: Voice input

## Tier-Based Features

### Freemium (Tier 1)
- 10 messages per day
- Basic market explanations
- Educational content access
- No voice features

### Market Hours Pro (Tier 2)
- 50 messages per day
- Portfolio analysis
- Strategy explanations
- Basic voice support

### Higher Tiers (3-7)
- Unlimited messages
- Advanced portfolio insights
- Custom strategy recommendations
- Full voice capabilities
- Priority response times

## Performance Requirements
- Response time: < 3 seconds for text
- Voice processing: < 5 seconds
- Context retrieval: < 500ms
- 99.9% uptime target
- Support 1000+ concurrent users

## Security & Privacy
- No storage of sensitive financial data
- Encrypted conversation history
- GDPR/CCPA compliant data handling
- Rate limiting and abuse prevention
- Audit logging for all interactions

## Success Metrics
- Average response time
- User satisfaction scores
- Conversation completion rates
- Educational content engagement
- Voice feature adoption rates

