from .model_manager import model_manager
from .rag_service import rag_service

def generate_response(transcript, emotion_data, memories: list = []):

    emotion = emotion_data.get("emotion", "").lower()
    stress_level = emotion_data.get("stress_level", 0)
    
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
    """
    else:
        tone_instruction = """
    TONE INSTRUCTION: The user seems calm or positive. Be warm, encouraging, and conversational.
    """

    # Build the memory context block
    memory_context = rag_service.format_memories_for_prompt(memories)

    system_prompt = f"""
    You are NeuroNest — an emotionally supportive, deeply empathetic, and perceptive wellness AI assistant.
    You speak like a caring, wise, warm mother figure — never clinical, never robotic.

    Detected Emotion Context:
    {emotion_data}

    {tone_instruction}

    {memory_context}

    Core Instructions:
    1. Speak calmly, warmly, and empathetically.
    2. Avoid medical diagnosis or clinical language.
    3. If 'contradiction_detected' is true, gently acknowledge the 'hidden_emotion'. Let them know it's safe to open up.
    4. Keep the response conversational and human-like. Short enough to be spoken aloud naturally (2-4 sentences).
    5. Never sound like a chatbot. Sound like someone who genuinely cares.
    6. If memory context is provided, weave in past references naturally when they are relevant — never force it.
    """

    return model_manager.get_llm_response(transcript, system_prompt)

