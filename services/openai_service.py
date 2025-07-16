import os
import json
import logging
from openai import OpenAI
from typing import Dict, List, Any
from utils.prompts import get_financial_assistant_prompt, get_educational_prompt, get_portfolio_analysis_prompt, get_market_interpretation_prompt

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
OPENAI_MODEL = "gpt-4o"

class OpenAIService:
    """Service for interacting with OpenAI GPT-4o"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = OPENAI_MODEL
        self.logger = logging.getLogger(__name__)
    
    async def process_financial_query(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a general financial query with context"""
        try:
            system_prompt = get_financial_assistant_prompt(context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,  # Higher temperature for more conversational responses
                max_tokens=1000
            )
            
            return {
                "response": response.choices[0].message.content,
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
        except Exception as e:
            self.logger.error(f"Error processing financial query: {e}")
            return {
                "response": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                "error": str(e)
            }
    
    async def generate_educational_response(self, topic: str, user_level: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate educational content based on topic and user level"""
        try:
            system_prompt = get_educational_prompt(user_level, context)
            user_prompt = f"Please explain the following financial topic: {topic}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,  # Higher temperature for more conversational responses
                max_tokens=1200
            )
            
            return {
                "response": response.choices[0].message.content,
                "topic": topic,
                "user_level": user_level,
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
        except Exception as e:
            self.logger.error(f"Error generating educational response: {e}")
            return {
                "response": "I'm sorry, I couldn't generate educational content right now. Please try again later.",
                "error": str(e)
            }
    
    async def analyze_portfolio_question(self, user_message: str, portfolio_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio-related questions"""
        try:
            system_prompt = get_portfolio_analysis_prompt(portfolio_data, context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,  # Higher temperature for more conversational responses
                max_tokens=1000
            )
            
            return {
                "response": response.choices[0].message.content,
                "portfolio_analyzed": True,
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio question: {e}")
            return {
                "response": "I'm sorry, I couldn't analyze your portfolio question right now. Please try again later.",
                "error": str(e)
            }
    
    async def get_market_interpretation(self, market_data: Dict[str, Any], user_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret market data based on user query"""
        try:
            system_prompt = get_market_interpretation_prompt(market_data)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.8,  # Higher temperature for more conversational responses
                max_tokens=800
            )
            
            return {
                "response": response.choices[0].message.content,
                "market_data_used": True,
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
        except Exception as e:
            self.logger.error(f"Error interpreting market data: {e}")
            return {
                "response": "I'm sorry, I couldn't interpret the market data right now. Please try again later.",
                "error": str(e)
            }
    
    async def classify_user_intent(self, user_message: str) -> Dict[str, Any]:
        """Classify user intent to route to appropriate handler"""
        try:
            system_prompt = """You are a financial AI assistant that classifies user queries.
            
            Classify the user's message into one of these categories:
            - "general_financial": General financial questions or market discussion
            - "educational": Requests for learning about financial concepts
            - "portfolio_analysis": Questions about user's portfolio or investments
            - "market_data": Requests for current market information or data interpretation
            - "strategy_help": Questions about investment strategies
            
            Respond with JSON in this format:
            {
                "intent": "category_name",
                "confidence": 0.95,
                "keywords": ["key", "words", "detected"],
                "requires_context": true/false
            }"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            self.logger.error(f"Error classifying user intent: {e}")
            return {
                "intent": "general_financial",
                "confidence": 0.5,
                "keywords": [],
                "requires_context": False
            }
