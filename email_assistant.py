#!/usr/bin/env python3
"""
AI Email Operations Assistant for Meta PyTorch Hackathon

A professional email processing system that analyzes, categorizes, and generates 
intelligent responses for email-related workflows using LiteLLM proxy.

Author: Meta PyTorch Hackathon Team
License: MIT
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailOperationsAssistant:
    """
    AI-powered Email Operations Assistant for intelligent email processing.
    
    Features:
    - Email classification (spam, important, promotional, etc.)
    - Auto-reply generation
    - Email thread summarization
    - Task extraction from emails
    """
    
    def __init__(self):
        """Initialize the email assistant with LiteLLM proxy configuration."""
        # Initialize OpenAI client using environment variables (REQUIRED)
        try:
            self.client = OpenAI(
                api_key=os.environ["API_KEY"],
                base_url=os.environ["API_BASE_URL"]
            )
            logger.info("✅ LiteLLM proxy client initialized successfully")
        except KeyError as e:
            logger.error(f"❌ Missing environment variable: {e}")
            raise RuntimeError("Required environment variables not set: API_KEY, API_BASE_URL")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            raise RuntimeError(f"Failed to initialize client: {e}")
    
    def _make_llm_call(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Make an API call to LiteLLM proxy for email analysis.
        
        Args:
            prompt: The prompt to send to LLM
            max_tokens: Maximum tokens for response
            
        Returns:
            str: LLM response text
        """
        try:
            logger.info("🔄 Making LLM API call...")
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[
                    {"role": "system", "content": "You are an expert email analysis assistant. Provide concise, accurate responses in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            logger.info("✅ LLM API call successful")
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM API call failed: {e}")
            raise RuntimeError(f"LLM call failed: {e}")
    
    def analyze_email(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Analyze email intent and category, then generate intelligent response.
        
        Args:
            subject: Email subject line
            body: Email body content
            
        Returns:
            Dict with category, summary, priority, and suggested_reply
        """
        # Combine subject and body for analysis
        email_content = f"Subject: {subject}\n\nBody: {body}"
        
        # Create analysis prompt
        prompt = f"""
Analyze the following email and provide a JSON response:

Email:
{email_content}

Required JSON format:
{{
  "category": "Important/Spam/Promotion/Personal/Work/Other",
  "summary": "Brief summary of the email (max 50 words)",
  "priority": "High/Medium/Low",
  "suggested_reply": "Professional response if needed (max 100 words)"
}}

Consider:
- Urgency indicators (deadlines, time-sensitive language)
- Sender relationship and context
- Action items or tasks mentioned
- Promotional language or spam characteristics
- Professional vs. personal tone
"""
        
        # Make LLM API call (REQUIRED FOR VALIDATION)
        logger.info("📧 Analyzing email...")
        llm_response = self._make_llm_call(prompt, max_tokens=300)
        
        try:
            # Parse JSON response
            result = json.loads(llm_response)
            
            # Validate required fields
            required_fields = ["category", "summary", "priority", "suggested_reply"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"⚠️ Missing field in LLM response: {field}")
                    # Provide default values for missing fields
                    if field == "category":
                        result[field] = "Other"
                    elif field == "summary":
                        result[field] = "Email analysis completed"
                    elif field == "priority":
                        result[field] = "Medium"
                    elif field == "suggested_reply":
                        result[field] = "Thank you for your email. I will review and respond accordingly."
            
            logger.info("✅ Email analysis completed successfully")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            # Return fallback response
            return {
                "category": "Other",
                "summary": "Email processed with analysis error",
                "priority": "Medium",
                "suggested_reply": "Thank you for your email. I will review it and respond appropriately."
            }
    
    def batch_analyze(self, emails: list) -> list:
        """
        Analyze multiple emails in batch for efficiency.
        
        Args:
            emails: List of dictionaries with 'subject' and 'body' keys
            
        Returns:
            List of analysis results
        """
        results = []
        logger.info(f"📦 Processing batch of {len(emails)} emails")
        
        for i, email in enumerate(emails, 1):
            logger.info(f"📧 Processing email {i}/{len(emails)}")
            result = self.analyze_email(email.get('subject', ''), email.get('body', ''))
            results.append(result)
        
        logger.info(f"✅ Batch analysis completed for {len(results)} emails")
        return results
    
    def extract_tasks(self, subject: str, body: str) -> list:
        """
        Extract action items and tasks from email content.
        
        Args:
            subject: Email subject line
            body: Email body content
            
        Returns:
            List of extracted tasks
        """
        email_content = f"Subject: {subject}\n\nBody: {body}"
        
        prompt = f"""
Extract action items and tasks from this email:

Email:
{email_content}

Return JSON format:
{{
  "tasks": [
    {{
      "task": "Task description",
      "priority": "High/Medium/Low",
      "deadline": "Date if mentioned, else null"
    }}
  ]
}}

Focus on:
- Action verbs (review, complete, send, schedule, etc.)
- Deadlines and time commitments
- Assignments or responsibilities
"""
        
        try:
            llm_response = self._make_llm_call(prompt, max_tokens=400)
            result = json.loads(llm_response)
            tasks = result.get('tasks', [])
            logger.info(f"✅ Extracted {len(tasks)} tasks from email")
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Task extraction failed: {e}")
            return []
    
    def classify_spam_probability(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Calculate probability of email being spam.
        
        Args:
            subject: Email subject line
            body: Email body content
            
        Returns:
            Dict with spam probability and confidence
        """
        email_content = f"Subject: {subject}\n\nBody: {body}"
        
        prompt = f"""
Analyze this email for spam characteristics:

Email:
{email_content}

Return JSON:
{{
  "spam_probability": 0.0-1.0,
  "confidence": 0.0-1.0,
  "indicators": ["list of spam indicators found"]
}}

Check for:
- Urgency language ("act now", "limited time")
- Suspicious links or domains
- Generic greetings
- Financial requests
- Poor grammar/spelling
"""
        
        try:
            llm_response = self._make_llm_call(prompt, max_tokens=300)
            result = json.loads(llm_response)
            
            # Ensure valid probability range
            spam_prob = max(0.0, min(1.0, result.get('spam_probability', 0.5)))
            confidence = max(0.0, min(1.0, result.get('confidence', 0.5)))
            
            result['spam_probability'] = spam_prob
            result['confidence'] = confidence
            
            logger.info(f"✅ Spam analysis completed: {spam_prob:.2f} probability")
            return result
            
        except Exception as e:
            logger.error(f"❌ Spam analysis failed: {e}")
            return {"spam_probability": 0.5, "confidence": 0.5, "indicators": ["analysis_error"]}

def main():
    """
    Main function demonstrating the Email Operations Assistant.
    """
    try:
        # Initialize the assistant
        assistant = EmailOperationsAssistant()
        logger.info("🚀 Email Operations Assistant initialized")
        
        # Example usage
        example_email = {
            "subject": "Meeting Reminder",
            "body": "Don't forget about project meeting tomorrow at 10 AM."
        }
        
        # Analyze the email (REQUIRED LLM CALL)
        result = assistant.analyze_email(
            example_email["subject"], 
            example_email["body"]
        )
        
        # Print result in required format
        print(json.dumps(result, indent=2))
        logger.info("✅ Demo completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
