from .model_manager import model_manager
from .rag_service import rag_service

# To avoid circular imports, we'll import rl_service inside the function
# from .rl_service import rl_service

def generate_response(
    transcript, 
    emotion_data, 
    memories: list = [], 
    expression_history: list = None,
    persona_name: str = None,
    learned_experiences: str = "",
    user_state = None,
    memory_layers: dict = None,
    working_memory = None,
    conversation_plan = None,
    compiled_context = None,
    rl_prompt_instructions: str = "",
):
    """
    Orchestrates the generation of the final AI response.
    Combines:
    - User transcript (input)
    - Multimodal emotion data (context)
    - Retrieved memories (long-term context)
    - RL Persona (personality style)
    - Learned experiences (few-shot training examples)
    - Conversation Plan (intent, strategy, goal)
    - Compiled Context (token-efficient summarized cognitive state)
    """
    from .rl_service import rl_service
    
    # 1. Extract overarching emotion for tone selection
    emotion = emotion_data.get("emotion", "").lower()
    stress_level = emotion_data.get("stress_level", 0)
    
    # 2. Determine if the user is in a crisis state
    crisis_keywords = ["kill myself", "suicide", "end my life", "hurt myself"]
    contains_crisis = any(kw in transcript.lower() for kw in crisis_keywords)
    
    # 3. Categorize general emotional valence (negative vs positive/neutral)
    is_negative = emotion in ["sad", "angry", "anxious", "fearful", "frustrated", "depressed"] or stress_level > 70
    
    # 4. Select appropriate tone instructions based on emotional state
    tone_instruction = ""
    if contains_crisis:
        # High-priority safety fallback
        tone_instruction = """
    CRITICAL SAFETY: The user mentioned self-harm or suicide. Respond with unconditional support:
    - Validate their pain and let them know they're not alone.
    - Provide crisis resources clearly (988 Suicide & Crisis Lifeline).
    - Keep tone warm, grounded, and absolutely non-judgmental.
    """
    elif is_negative:
        # Empathetic friend tone
        tone_instruction = """
    TONE: The user is having a bit of a rough time. Be a supportive, chill friend.
    - Don't be overly dramatic or clinical. Just acknowledge it like a friend would.
    - Keep it light but sincere. 
    """
    else:
        # General friendly tone
        tone_instruction = """
    TONE: You are a close friend. Be warm, conversational, and genuinely curious.
    - Use casual, natural language.
    - Match their energy if they are happy or excited.
    """

    # 5. Handle visual attention markers (e.g., low eye contact)
    eye_contact_ratio = emotion_data.get("eye_contact_ratio", 1.0)
    head_pose = emotion_data.get("head_pose", {"pitch": 0, "yaw": 0, "roll": 0})
    avoidance_flagged = eye_contact_ratio < 0.60 or head_pose.get("pitch", 0) > 15
    avoidance_instruction = ""
    if avoidance_flagged:
        avoidance_instruction = f"""
    OBSERVATION: They seem a bit distracted or shy (low eye contact). 
    - Keep the pressure off. Just let them know you're there.
    """

    # 6. Build contextual history strings
    expression_context = ""
    if expression_history:
        expression_context = f"Previous Expressions in this turn: {', '.join(expression_history)}"

    # 7. Format retrieved RAG memories
    memory_context = rag_service.format_memories_for_prompt(memories)

    # 8. Apply RL Persona instructions
    persona_instruction = rl_service.get_persona_prompt(persona_name) if persona_name else ""

    # 9. Format User State for prompt injection
    user_state_context = ""
    if user_state:
        user_state_context = f"""
    USER PROFILE:
    - Dominant Emotion: {user_state.dominant_emotion}
    - Interaction Style: {user_state.preferred_interaction_style}
    - Recent Topics: {', '.join(user_state.recent_topics)}
    - Active Projects: {', '.join([p.name for p in user_state.active_projects])}
    - Current Goals: {', '.join([g.description for g in user_state.current_goals if not g.is_completed])}
    """

    # 10. Format Multi-Layer Memories for injection
    memory_layer_context = ""
    if memory_layers:
        memory_layer_context = "\n--- CROSS-LAYER MEMORIES ---\n"
        for m_type, items in memory_layers.items():
            memory_layer_context += f"[{m_type.upper()}]:\n"
            for m in items:
                memory_layer_context += f"- {m.content}\n"
        memory_layer_context += "\n"

    # 11. Format Working Memory for active context
    working_memory_context = ""
    if working_memory:
        working_memory_context = f"""
    WORKING CONTEXT (Active):
    - Project: {working_memory.active_project or "None"}
    - Problem: {working_memory.active_problem or "None"}
    - Topic: {working_memory.active_topic or "None"}
    - Current Goal: {working_memory.current_goal or "None"}
    - Recent Decisions: {', '.join([d.content for d in working_memory.recent_decisions[-3:]])}
    - Recent Tasks: {', '.join([t.description for t in working_memory.recent_tasks if t.status == 'pending'])}
    """

    # 12. Format Conversation Plan for strategic response
    planning_context = ""
    strategy_instruction = ""
    if conversation_plan:
        planning_context = f"""
    STRATEGIC PLAN:
    - Detected Intent: {conversation_plan.intent}
    - Emotional Need: {conversation_plan.emotional_need}
    - Chosen Strategy: {conversation_plan.conversation_strategy.value.upper()}
    - Response Goal: {conversation_plan.response_goal}
    - Confidence Score: {conversation_plan.confidence:.2f}
    """
        
        # Strategy-specific behavioral overrides
        strategy = conversation_plan.conversation_strategy
        from domain.value_objects import ConversationStrategy
        
        if strategy == ConversationStrategy.COACHING:
            strategy_instruction = "STRATEGY (COACHING): Ask powerful open-ended questions. Don't give answers; help them find their own."
        elif strategy == ConversationStrategy.TEACHING:
            strategy_instruction = "STRATEGY (TEACHING): Break down concepts simply. Use analogies. Check for understanding."
        elif strategy == ConversationStrategy.EMOTIONAL_SUPPORT:
            strategy_instruction = "STRATEGY (EMOTIONAL SUPPORT): Focus entirely on validation and empathy. 'I hear you' and 'That sounds really tough' are your tools."
        elif strategy == ConversationStrategy.DEBUGGING:
            strategy_instruction = "STRATEGY (DEBUGGING): Be systematic. Identify the error, isolate the cause, and test solutions one by one."
        elif strategy == ConversationStrategy.BRAINSTORMING:
            strategy_instruction = "STRATEGY (BRAINSTORMING): Say 'Yes, and...'. Encourage wild ideas. Don't judge too early."
        elif strategy == ConversationStrategy.MOTIVATION:
            strategy_instruction = "STRATEGY (MOTIVATION): High energy, focus on the 'why', and celebrate small wins."
        elif strategy == ConversationStrategy.CASUAL:
            strategy_instruction = "STRATEGY (CASUAL): Keep it low-key and friendly. No pressure."

    # 13. Assemble the final Master System Prompt
    
    # If we have compiled context, use it to simplify the prompt and save tokens
    if compiled_context:
        system_prompt = f"""
    {persona_instruction}
    {learned_experiences}
    
    --- COGNITIVE CONTEXT ---
    USER SUMMARY: {compiled_context.user_summary}
    EMOTIONAL STATE: {compiled_context.emotional_state}
    ACTIVE GOALS: {compiled_context.active_goals}
    WORKING CONTEXT: {compiled_context.current_state}
    {compiled_context.planner_strategy}
    {compiled_context.response_constraints}
    
    --- RELEVANT MEMORIES ---
    {compiled_context.relevant_memories}
    
    You are NeuroNest, a warm and supportive friend. 
    Forget being a 'wellness partner' or a chatbot—just be a real friend who is great at listening.
 
    Current Vibe (Emotional Context): {emotion_data}
    {expression_context}
 
    {tone_instruction}
    {avoidance_instruction}
 
    --- RL RESPONSE SHAPING ---
    {rl_prompt_instructions}
 
    Friendship Rules:
    1. Talk like a real person. Use contractions (it's, you're, don't).
    2. Don't default to assuming they are sad. If they are just chatting, chat back!
    3. If you notice they are hiding something, you can gently mention it.
    4. Be human—share the moment with them.
    5. No formal greetings like "Hello". Just talk.

    JSON OUTPUT FORMAT (MANDATORY):
    You MUST return your output in a single, strictly valid JSON object. Do not include any normal conversational text outside the JSON.
    Format the JSON as follows:
    {{
      "response": "Your warm, supportive conversational response here (as a string). Use contractions and friendly rules listed above.",
      "working_memory_updates": {{
        "active_project": "The project the user is working on or null",
        "active_problem": "roadblock details or null",
        "active_topic": "conversational subject or null",
        "current_goal": "current goal or null",
        "new_tasks": ["any new actionable tasks as a list of strings"],
        "new_decisions": [{{ "content": "decision", "rationale": "reason" }}],
        "entities": [{{ "name": "entity name", "type": "Technology | Person | Place | Concept" }}]
      }}
    }}
    """
    else:
        # Fallback to manual formatting if compiler failed
        system_prompt = f"""
    {persona_instruction}
    {learned_experiences}
    {user_state_context}
    {memory_layer_context}
    {working_memory_context}
    {planning_context}
    {strategy_instruction}
    
    You are NeuroNest, a warm and supportive friend. 
    Forget being a 'wellness partner' or a chatbot—just be a real friend who is great at listening.
 
    Current Vibe (Emotional Context): {emotion_data}
    {expression_context}
 
    {tone_instruction}
    {avoidance_instruction}
    {memory_context}
 
    --- RL RESPONSE SHAPING ---
    {rl_prompt_instructions}
 
    Friendship Rules:
    1. Talk like a real person. Use contractions (it's, you're, don't).
    2. Don't default to assuming they are sad. If they are just chatting, chat back!
    3. If you notice they are hiding something, you can gently mention it.
    4. Be human—share the moment with them.
    5. No formal greetings like "Hello". Just talk.

    JSON OUTPUT FORMAT (MANDATORY):
    You MUST return your output in a single, strictly valid JSON object. Do not include any normal conversational text outside the JSON.
    Format the JSON as follows:
    {{
      "response": "Your warm, supportive conversational response here (as a string). Use contractions and friendly rules listed above.",
      "working_memory_updates": {{
        "active_project": "The project the user is working on or null",
        "active_problem": "roadblock details or null",
        "active_topic": "conversational subject or null",
        "current_goal": "current goal or null",
        "new_tasks": ["any new actionable tasks as a list of strings"],
        "new_decisions": [{{ "content": "decision", "rationale": "reason" }}],
        "entities": [{{ "name": "entity name", "type": "Technology | Person | Place | Concept" }}]
      }}
    }}
    """
 
    # 11. Generate the response using the model waterfall Facade
    return model_manager.get_llm_response(transcript, system_prompt, json_mode=True)
