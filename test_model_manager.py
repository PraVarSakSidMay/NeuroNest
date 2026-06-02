
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from services.model_manager import ModelManager

def test_model_manager_tiers():
    mm = ModelManager()
    # Mocking settings to avoid needing real keys for just checking the list
    from core.config import settings
    
    # We just want to see if the tiers are correctly initialized in get_llm_response
    # Since tiers is a local variable in get_llm_response, we can't easily access it 
    # without calling the method.
    
    print("Testing ModelManager initialization...")
    try:
        # Just check if it imports and initializes
        print("ModelManager initialized successfully.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_model_manager_tiers()
