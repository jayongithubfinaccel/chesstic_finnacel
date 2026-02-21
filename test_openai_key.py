"""
Test script to verify OpenAI API key is working.
This script tests the API key without running the full analytics.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_key():
    """Test if OpenAI API key is configured and working."""
    
    # Check if API key is set
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not api_key:
        print("❌ OPENAI_API_KEY is not set in environment variables")
        print("   Please add it to your .env file")
        return False
    
    print(f"✓ API key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Try to import openai and test connection
    try:
        import openai
        print("✓ OpenAI library imported successfully")
    except ImportError:
        print("❌ OpenAI library not installed")
        print("   Run: uv add openai")
        return False
    
    # Test API connection with a simple request
    try:
        client = openai.OpenAI(api_key=api_key)
        
        print("\nTesting API connection with a simple request...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Say 'API key is working!' if you can read this."}
            ],
            max_tokens=20,
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        print(f"✓ API Response: {result}")
        print(f"✓ Tokens used: {response.usage.total_tokens}")
        print(f"✓ Model: {response.model}")
        
        print("\n✅ OpenAI API key is working correctly!")
        return True
        
    except openai.AuthenticationError:
        print("\n❌ Authentication failed - Invalid API key")
        print("   Please check your OPENAI_API_KEY in .env file")
        return False
    except openai.RateLimitError:
        print("\n⚠️ Rate limit exceeded - API key is valid but quota exceeded")
        print("   Please check your OpenAI account billing")
        return False
    except Exception as e:
        print(f"\n❌ Error testing API: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("OpenAI API Key Test")
    print("=" * 60)
    
    success = test_openai_key()
    
    print("\n" + "=" * 60)
    sys.exit(0 if success else 1)
