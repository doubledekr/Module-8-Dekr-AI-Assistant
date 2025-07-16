# Dekr AI Assistant

## Overview

Dekr AI Assistant is a sophisticated financial AI chat application built with Flask that provides intelligent conversational support for users. The system helps users understand market data, navigate financial concepts, get portfolio insights, and receive personalized financial education. The application features a tiered user system with different capabilities based on subscription levels.

## User Preferences

Preferred communication style: Simple, everyday language.
Tool behavior: Must be conversational regardless of user tier (July 16, 2025).

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (configurable to PostgreSQL via DATABASE_URL)
- **Caching**: Redis for session management and rate limiting
- **AI Integration**: OpenAI GPT-4o for conversational AI
- **Session Management**: Flask sessions with Redis backing

### Frontend Architecture
- **Template Engine**: Jinja2 templates
- **UI Framework**: Bootstrap 5 (dark theme)
- **JavaScript**: Vanilla JavaScript with ES6 classes
- **Styling**: CSS custom properties with Bootstrap integration
- **Icons**: Font Awesome 6

### Data Storage
- **Primary Database**: SQLite (development) / PostgreSQL (production)
- **Cache Layer**: Redis for temporary data, rate limiting, and session storage
- **Session Storage**: Server-side sessions with Redis persistence

## Key Components

### Models (`models.py`)
- **ChatSession**: Manages user chat sessions with context data and user tier information
- **ChatMessage**: Stores individual chat messages with AI responses and metadata
- **UserContext**: Tracks user preferences, portfolio data, and learning progress

### Services Layer
- **OpenAIService**: Handles GPT-4o integration for financial queries and educational content
- **ContextService**: Manages user context and conversation history
- **FinancialDataService**: Integrates with financial APIs (Polygon, MarketAux)
- **CacheService**: Redis-based caching for API responses and frequently accessed data

### API Routes (`api/chat_routes.py`)
- **POST /api/v1/chat/message**: Send messages to AI assistant
- **GET /api/v1/chat/history**: Retrieve conversation history
- **POST /api/v1/chat/context/update**: Update user context
- **GET /api/v1/chat/suggestions**: Get conversation suggestions

### Utilities
- **RateLimiter**: Tier-based rate limiting (daily and per-minute limits)
- **Validators**: Input validation for messages and session data
- **Prompts**: Dynamic prompt generation based on user tier and context

## Data Flow

1. **User Interaction**: User sends message through chat interface
2. **Validation**: Message validated for content and format
3. **Rate Limiting**: Check against user tier limits
4. **Context Retrieval**: Gather user context, session history, and preferences
5. **AI Processing**: Send to OpenAI GPT-4o with appropriate prompts
6. **Response Processing**: Format and validate AI response
7. **Storage**: Save message and response to database
8. **Caching**: Cache relevant data for performance
9. **UI Update**: Return response to frontend for display

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4o for conversational AI and financial analysis
- **Model**: "gpt-4o" (latest OpenAI model as of May 2024)

### Financial Data APIs
- **Polygon API**: Stock quotes and market data
- **MarketAux API**: Financial news and additional market data

### Infrastructure
- **Redis**: Session management, caching, and rate limiting
- **Flask Extensions**: SQLAlchemy, CORS, Limiter

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6**: Icons and visual elements

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database, local Redis instance
- **Production**: PostgreSQL database, Redis cluster
- **Environment Variables**: 
  - `DATABASE_URL`: Database connection string
  - `REDIS_URL`: Redis connection string
  - `OPENAI_API_KEY`: OpenAI API credentials
  - `POLYGON_API_KEY`: Financial data API key
  - `MARKETAUX_API_KEY`: News API key
  - `SESSION_SECRET`: Session encryption key

### Scaling Considerations
- **Database**: Supports both SQLite (development) and PostgreSQL (production)
- **Caching**: Redis-based caching for improved performance
- **Rate Limiting**: Tier-based limits to manage API costs
- **Threading**: Thread pool executor for async operations

### Security Features
- **Input Validation**: Comprehensive message and session validation
- **Rate Limiting**: Prevents abuse with tier-based limits
- **Session Management**: Secure session handling with Redis
- **Content Filtering**: Harmful content detection and filtering

The application is designed to be production-ready with proper error handling, logging, and scalability considerations while maintaining a user-friendly interface for financial education and assistance.