import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import re
import requests  # Import requests for making API calls

from pydantic import BaseModel, validator, ValidationError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# --- Removed OpenAI client ---

# Define the JSON schema for the Gemini API
# This forces the model to return clean JSON matching our pydantic model
INVOICE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "invoice_number": {"type": "STRING"},
        "invoice_date": {"type": "STRING", "description": "The invoice date, formatted as YYYY-MM-DD. Handle formats like %d/%m/%Y, %m/%d/%Y, etc."},
        "amount": {"type": "NUMBER", "description": "The total amount as a float, stripping currency symbols."},
        "due_date": {"type": "STRING", "description": "The due date, formatted as YYYY-MM-DD. Handle formats like %d/%m/%Y, %m/%d/%Y, etc."}
    },
    "propertyOrdering": ["invoice_number", "invoice_date", "amount", "due_date"]
}


class InvoiceData(BaseModel):
    """Pydantic model for invoice data validation."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[str] = None

    @validator('invoice_date', 'due_date', pre=True)
    def parse_date(cls, v):
        if not v:
            return None
        try:
            # Try to parse various date formats
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"):
                try:
                    return datetime.strptime(str(v).strip(), fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    @validator('amount', pre=True)
    def parse_amount(cls, v):
        if v is None:
            return None
        try:
            if isinstance(v, (int, float)):
                return float(v)
            # Remove currency symbols and thousands separators
            return float(re.sub(r'[^\d.]', '', str(v)))
        except (ValueError, TypeError):
            return None

def extract_with_llm(text: str) -> Dict[str, Any]:
    """Extract invoice data using Google's Gemini API with JSON schema."""
    
    # Get the API key from the environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found in .env file. LLM extraction will be skipped.")
        return {}
        
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    # Truncate text to avoid overly large payloads
    truncated_text = text[:15000] 

    system_prompt = (
        "You are an expert at extracting invoice information. "
        "Extract the invoice number, invoice date, total amount, and due date from the provided text. "
        "Dates must be formatted as YYYY-MM-DD."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Extract invoice data from this text:\n\n{truncated_text}"}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": INVOICE_SCHEMA,
            "temperature": 0.0  # Make it deterministic
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Make the API call
        response = requests.post(
            api_url, 
            headers=headers, 
            data=json.dumps(payload), 
            timeout=30.0  # 30-second timeout
        )
        
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        
        # Safely extract the JSON string from the response
        candidate = result.get("candidates", [{}])[0]
        content_part = candidate.get("content", {}).get("parts", [{}])[0]
        json_string = content_part.get("text", "{}")
        
        return json.loads(json_string)

    except requests.exceptions.RequestException as e:
        logger.warning(f"Gemini API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
             logger.warning(f"Gemini API response body: {e.response.text}")
        return {}
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to parse Gemini API response: {str(e)}")
        return {}
    except Exception as e:
        logger.warning(f"LLM extraction failed unexpectedly: {str(e)}")
        return {}

def extract_with_regex(text: str) -> Dict[str, Any]:
    """Fallback method using regex patterns to extract invoice data."""
    data = {
        "invoice_number": None,
        "invoice_date": None,
        "amount": None,
        "due_date": None
    }
    
    # Invoice number patterns (Corrected regex)
    invoice_patterns = [
        r'(?:invoice|bill|receipt)[^\n]*?(?:no\.?|number|#)[\s:]*([A-Z0-9-]+)',
        r'(?:invoice|bill|receipt)[^\n]*(\d{4,})',
        r'(?:^|\s)(?:#|INV-?)(\d+)(?:\s|$)'
    ]
    
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_number"] = match.group(1).strip()
            break
    
    # Date patterns (Corrected regex)
    date_patterns = [
        r'(?:date|issued|invoice date)[^\n]*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:date|issued|invoice date)[^\n]*?(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
    ]
    
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    
    # Parse dates
    parsed_dates = []
    for date_str in dates:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"):
            try:
                parsed = datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                parsed_dates.append(parsed)
                break
            except ValueError:
                continue
    
    if parsed_dates:
        data["invoice_date"] = parsed_dates[0]
        if len(parsed_dates) > 1:
            data["due_date"] = parsed_dates[-1]
    
    # Amount patterns (Corrected regex)
    amount_patterns = [
        r'(?:total|amount|balance).*?[\$€£¥₹]\s*(\d+[\d,]*\.?\d*)',
        r'(?:total|amount|balance).*?(\d+[\d,]*\.?\d+)\s*(?:USD|EUR|GBP|INR|JPY|CAD|AUD|NZD)'
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                amounts = [float(m.replace(',', '')) for m in matches]
                data["amount"] = max(amounts)  # Take the largest amount found
                break
            except (ValueError, IndexError):
                continue
    
    return data

def extract_invoice_data(text: str) -> InvoiceData:
    """
    Extract structured invoice data from text using LLM with fallback to regex.
    
    Args:
        text: Raw text extracted from the invoice
        
    Returns:
        An InvoiceData Pydantic model instance.
    """
    if not text.strip():
        raise ValueError("Empty text provided for invoice extraction")
    
    # Try LLM extraction first
    llm_data = extract_with_llm(text)
    
    # Fallback to regex if LLM fails or returns empty
    if not any(llm_data.values()):
        logger.info("LLM extraction failed or returned empty. Falling back to regex.")
        llm_data = extract_with_regex(text)
    
    # Validate and clean the data
    try:
        validated_data = InvoiceData(**llm_data)
        return validated_data  # <-- CHANGED: Return the Pydantic model instance
    except ValidationError as e:
        logger.warning(f"Pydantic validation failed: {e}. Returning raw data as model.")
        # If validation fails, return a model with the raw (but filtered) data
        safe_data = {k: v for k, v in llm_data.items() if v is not None and k in InvoiceData.__fields__}
        return InvoiceData(**safe_data) # <-- CHANGED: Return Pydantic model instance

