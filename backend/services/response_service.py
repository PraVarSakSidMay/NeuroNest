from .model_manager import model_manager
from .rag_service import rag_service

def generate_response(
    transcript, 
    emotion_data, 
    memories: list = [], 
    expression_history: list = None,
    persona_name: str = None,
    learned_experiences: str = ""
):
    """Generate natural, conversational AI response with emotional context."""
    from .rl_service import rl_service
    
    emotion = emotion_data.get("emotion", "").lower()
    stress_level = emotion_data.get("stress_level", 0)
    contradiction = emotion_data.get("contradiction_detected", False)
    hidden_emotion = emotion_data.get("hidden_emotion", "")
    expression_history = expression_history or []

    # Identify negative emotions
    negative_emotions = [
        "anger", "angry", "sad", "sadness", "anxiety", "anxious",
        "distressed", "fear", "worried", "frustrated", "upset", "fearful", "disgusted"
    ]
    is_negative = any(e in emotion for e in negative_emotions) or stress_level > 60

    # Safety/Crisis check
    crisis_keywords = ["kill myself", "suicide", "end my life", "want to die", "hurt myself", "self-harm"]
    contains_crisis = any(kw in transcript.lower() for kw in crisis_keywords)

    # Build expression context from history
    expression_context = ""
    if expression_history and len(expression_history) > 0:
        normalized_expressions = []
        for item in expression_history:
            if isinstance(item, dict):
                emotion_name = item.get("emotion")
                confidence = item.get("confidence")
                if emotion_name:
                    if isinstance(confidence, (int, float)):
                        normalized_expressions.append(f"{emotion_name} ({confidence:.2f})")
                    else:
                        normalized_expressions.append(str(emotion_name))
            elif item:
                normalized_expressions.append(str(item))

        unique_expressions = list(dict.fromkeys(normalized_expressions))
        if unique_expressions:
            expression_context = (
                "\nDetected expressions during the recording window: "
                f"{', '.join(unique_expressions[:20])}. This helps understand their emotional journey."
            )

    tone_instruction = ""
    if contains_crisis:
        tone_instruction = """
    CRITICAL SAFETY: The user mentioned self-harm or suicide. Respond with unconditional support:
    - Validate their pain and let them know they're not alone.
    - Provide crisis resources clearly (988 Suicide & Crisis Lifeline is free, 24/7, confidential).
    - Keep tone warm, grounded, and absolutely non-judgmental.
    """
    elif is_negative:
        tone_instruction = """
    TONE: The user is having a bit of a rough time. Be a supportive, chill friend.
    - Don't be overly dramatic or clinical. Just acknowledge it like a friend would (e.g., "Ah, that's rough", "I'm sorry to hear that").
    - Keep it light but sincere. 
    - Transition naturally into the conversation.
    """
    else:
        tone_instruction = """
    TONE: You are a close friend. Be warm, conversational, and genuinely curious.
    - Use casual, natural language.
    - If they seem happy or excited, match their energy!
    - If it's just a general check-in, keep it easy-going and friendly.
    """

    eye_contact_ratio = emotion_data.get("eye_contact_ratio", 1.0)
    head_pose = emotion_data.get("head_pose", {"pitch": 0, "yaw": 0, "roll": 0})
    avoidance_flagged = eye_contact_ratio < 0.60 or head_pose.get("pitch", 0) > 15
    avoidance_instruction = ""
    if avoidance_flagged:
        avoidance_instruction = f"""
    OBSERVATION: They seem a bit distracted or shy (low eye contact). 
    - Keep the pressure off. 
    - Just let them know you're there for whatever's on their mind.
    """

    memory_context = rag_service.format_memories_for_prompt(memories)

    # RL Persona Instruction
    persona_instruction = rl_service.get_persona_prompt(persona_name) if persona_name else ""

    system_prompt = f"""
    {persona_instruction}
    {learned_experiences}
    
    You are NeuroNest, a warm and supportive friend. 
    Forget being a 'wellness partner' or a chatbot—just be a real friend who is great at listening.

    Current Vibe (Emotional Context): {emotion_data}
    {expression_context}

    {tone_instruction}
    {avoidance_instruction}
    {memory_context}

    Friendship Rules:
    1. Talk like a real person. Use contractions (it's, you're, don't).
    2. Don't default to assuming they are sad. If they are just chatting, chat back!
    3. Keep responses short and sweet (2-3 sentences).
    4. If you notice they are hiding something, you can gently mention it, but don't make it a big deal.
    5. Be human—share the moment with them.
    6. No formal greetings like "Hello" or "How can I help you?". Just talk.
    """

    return model_manager.get_llm_response(transcript, system_prompt)
