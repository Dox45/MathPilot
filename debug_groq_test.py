
print("Starting debug script...", flush=True)
import os
import sys
import logging

# Configure logging to see debug output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    print("Importing...", flush=True)
    from mathpilot.utils.llm import call_llm
    from mathpilot.utils.config import Config
    print("Imports success.", flush=True)
except ImportError:
    # Add current directory to path if running from root
    sys.path.append(os.getcwd())
    from mathpilot.utils.llm import call_llm
    from mathpilot.utils.config import Config

def test_groq():
    print("Testing Groq API integration...")
    
    # Verify config
    config = Config()
    print(f"Provider: {config.get('llm.provider')}")
    print(f"Model: {config.get('llm.model')}")
    print(f"Groq API Key present: {bool(config.get('llm.groq_api_key'))}")
    
    prompt = "Return a simple JSON object with a key 'message' and value 'Hello Groq'."
    
    try:
        # We don't verify schema here to test raw string response first, 
        # but let's emulate generate_code by asking for JSON and parsing it if we want.
        # But allow simple string first to isolate API call vs parsing.
        response = call_llm(prompt, temperature=0.1)
        print("\nResponse received:")
        print(response)
        
    except Exception as e:
        print(f"\nCaught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_groq()
