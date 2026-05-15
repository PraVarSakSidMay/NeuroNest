import os
from deepgram import DeepgramClient
from dotenv import load_dotenv

# Force reload of environment variables
if os.path.exists(".env"):
    load_dotenv(".env", override=True)
elif os.path.exists("backend/.env"):
    load_dotenv("backend/.env", override=True)

api_key = os.getenv("DEEPGRAM_API_KEY")

print(f"Deepgram TTS Test (SDK 7.x style)")
print(f"Using Key: {api_key[:4]}...{api_key[-4:] if api_key else 'None'}")

if not api_key:
    print("Error: DEEPGRAM_API_KEY not found.")
    exit(1)

try:
    client = DeepgramClient(api_key=api_key)
    filename = "test_deepgram.mp3"
    
    if os.path.exists(filename):
        os.remove(filename)

    print("Sending TTS request using client.speak.v1.audio.generate (encoding='mp3')...")
    # generate returns an iterator of bytes
    audio_iterator = client.speak.v1.audio.generate(
        text="Hello, this is a test of the new Deepgram SDK 7.x with the new API key.",
        model="aura-2-thalia-en",
        encoding="mp3"
    )
    
    with open(filename, "wb") as f:
        for chunk in audio_iterator:
            f.write(chunk)
    
    if os.path.exists(filename) and os.path.getsize(filename) > 1000:
        print(f"SUCCESS! File saved to {filename}")
        print(f"   Size: {os.path.getsize(filename)} bytes")
    else:
        print(f"FAILED: File not found or too small ({os.path.getsize(filename) if os.path.exists(filename) else 0} bytes).")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
