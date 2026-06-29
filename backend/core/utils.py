import json
from typing import Optional, Any
from core.logger import logger

def parse_robust_json(text: str) -> Optional[Any]:
    """
    Robustly parses a JSON object/list from a string that might contain
    markdown formatting, conversational prefixes/suffixes, or control characters.
    """
    if not text:
        return None
    
    text = text.strip()
    
    # 1. Try raw parsing first (with strict=False to allow raw newlines/control characters)
    try:
        return json.loads(text, strict=False)
    except Exception:
        pass
        
    # 2. Try stripping markdown blocks if present (```json ... ``` or ``` ... ```)
    cleaned = text
    if "```json" in cleaned:
        try:
            candidate = cleaned.split("```json")[1].split("```")[0].strip()
            return json.loads(candidate, strict=False)
        except Exception:
            pass
    if "```" in cleaned:
        try:
            candidate = cleaned.split("```")[1].split("```")[0].strip()
            return json.loads(candidate, strict=False)
        except Exception:
            pass

    # 3. Find the first occurrence of '{' and last occurrence of '}'
    start_idx = cleaned.find('{')
    end_idx = cleaned.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_candidate = cleaned[start_idx:end_idx+1]
        try:
            return json.loads(json_candidate, strict=False)
        except Exception as e:
            logger.debug(f"parse_robust_json: Failed inner JSON block parsing: {e}")
            pass
            
    # 4. Find the first occurrence of '[' and last occurrence of ']' (for lists)
    start_idx = cleaned.find('[')
    end_idx = cleaned.rfind(']')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_candidate = cleaned[start_idx:end_idx+1]
        try:
            return json.loads(json_candidate, strict=False)
        except Exception:
            pass
            
    return None
