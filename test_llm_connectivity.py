import os
import litellm
from dotenv import load_dotenv

load_dotenv()

def test_provider(name, model, api_base=None, api_key=None):
    print(f"\n--- Testing Provider: {name} ---")
    print(f"Model: {model}")
    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Hello, respond with 'READY' if you can hear me."}],
            api_base=api_base,
            api_key=api_key or os.getenv(f"{name.upper()}_API_KEY"),
            timeout=30
        )
        content = response.choices[0].message.content.strip()
        print(f"[SUCCESS] {name} responded: {content}")
        return True
    except Exception as e:
        print(f"[FAIL] {name} error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Multi-LLM Connectivity Diagnostics...")
    
    # Test Groq (Primary)
    test_provider("Groq", "groq/llama-3.3-70b-versatile")
    
    # Test Mistral (Fallback 1)
    test_provider("Mistral", "mistral/mistral-large-latest")
    
    # Test Ollama Cloud (Fallback 2 / gpt-oss)
    test_provider(
        "Ollama Cloud", 
        f"ollama/{os.getenv('OLLAMA_MODEL', 'gpt-oss:12b')}",
        api_base=os.getenv("OLLAMA_API_BASE"),
        api_key=os.getenv("OLLAMA_API_KEY")
    )
    
    print("\n--- Diagnostics Complete ---")
