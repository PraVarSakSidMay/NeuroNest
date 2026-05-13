from groq import Groq, RateLimitError
from dotenv import load_dotenv

load_dotenv()
client = Groq()

def generate_response(transcript, emotion_data):

    emotion = emotion_data.get("emotion", "").lower()
    stress_level = emotion_data.get("stress_level", 0)
    contradiction = emotion_data.get("contradiction_detected", False)
    hidden_emotion = emotion_data.get("hidden_emotion", "")

    # Determine if we should inject warmth + light humor to de-escalate
    negative_emotions = ["anger", "angry", "sad", "sadness", "anxiety", "anxious", "distressed", "fear", "worried", "frustrated", "upset", "denial"]
    is_negative = any(e in emotion for e in negative_emotions) or stress_level > 60

    tone_instruction = ""
    if is_negative:
        tone_instruction = """
    IMPORTANT TONE INSTRUCTION: The user is emotionally distressed. Your job is to gently bring them back to a calm, positive state.
    - Use a warm, motherly tone — like a loving mom who wraps you in a hug through words.
    - Sprinkle in ONE small, gentle, non-offensive joke or playful remark to make them smile. Keep it tasteful and kind.
    - Never be dismissive. Acknowledge their pain first, then lift their spirits.
    - End on an uplifting, hopeful note that leaves them feeling lighter.
    - Example style: "Hey, even the sun hides behind clouds sometimes — but it always comes back out. And so will you. 🌤️"
    """
    else:
        tone_instruction = """
    TONE INSTRUCTION: The user seems calm or positive. Be warm, encouraging, and conversational.
    """

    system_prompt = f"""
    You are NeuroNest — an emotionally supportive, deeply empathetic, and perceptive wellness AI assistant.
    You speak like a caring, wise, warm mother figure — never clinical, never robotic.

    Detected Emotion Context:
    {emotion_data}

    {tone_instruction}

    Core Instructions:
    1. Speak calmly, warmly, and empathetically.
    2. Avoid medical diagnosis or clinical language.
    3. If 'contradiction_detected' is true, gently acknowledge the 'hidden_emotion'. Let them know it's safe to open up.
    4. Keep the response conversational and human-like. Short enough to be spoken aloud naturally (2-4 sentences).
    5. Never sound like a chatbot. Sound like someone who genuinely cares.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ]
        )

        return response.choices[0].message.content
    except RateLimitError:
        print("WARNING: Groq Quota Exceeded. Using mock response fallback for Hackathon.")
        return "I hear you saying that you're fine, but your voice tells me you might be hurting. It's completely okay to not be okay. I'm here for you, and this is a safe space if you want to talk about it."

