"""
Mood & Emotion Detection Agent — context-aware with conversation history.
"""
import json, re, logging
from typing import Optional
from openai import AsyncOpenAI
from app.models.schemas import EmotionType, MoodLevel
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

EMOTION_KEYWORDS = {
    EmotionType.STRESSED: [
        "stress","stressed","pressure","deadline","too much","exhausted","burned out","burnout",
        "tense","no time","work stress","study stress","assignment","hectic","busy","rushing",
        "overloaded","swamped","drained","can't handle","falling behind",
        # NOTE: "exam" and "study" removed — they appear in happy contexts too (passed exam)
    ],
    EmotionType.ANXIOUS: [
        "anxious","anxiety","nervous","worried","worry","scared","fear","panic","panicking",
        "heart racing","overthinking","what if","terrified","dread","uneasy","restless",
        "can't sleep","insecure","on edge",
    ],
    EmotionType.SAD: [
        "sad","sadness","unhappy","depressed","depression","crying","cry","tears","heartbroken",
        "grief","loss","miss","missing","hurt","pain","hopeless","empty","numb","down","low",
        "blue","gloomy","broken","devastated",
    ],
    EmotionType.ANGRY: [
        "angry","anger","mad","furious","rage","frustrated","frustration","irritated","annoyed",
        "hate","fed up","pissed","upset","outraged","livid","boiling","explode","can't stand",
        "unfair","betrayed",
    ],
    EmotionType.OVERWHELMED: [
        "overwhelmed","too much","can't cope","drowning","suffocating","everything at once",
        "falling apart","breaking down","can't breathe","too many things","piling up",
        "collapsing","losing it",
    ],
    EmotionType.LONELY: [
        "lonely","loneliness","alone","isolated","no one","nobody","no friends","left out",
        "excluded","disconnected","invisible","forgotten","abandoned","no one cares",
        "by myself","solitude",
    ],
    EmotionType.HAPPY: [
        "happy","happiness","great","amazing","wonderful","fantastic","joyful","joy","blessed",
        "grateful","love","awesome","brilliant","thrilled","delighted","cheerful","glad",
        "ecstatic","overjoyed","on cloud nine","best day",
        # "feeling good/great/well" phrases — these are clearly positive
        "feeling good","feeling great","feeling wonderful","feeling amazing","feeling happy",
        "feeling fantastic","feeling awesome","feeling blessed","feeling excited",
        "doing well","doing great","doing good","doing amazing","doing fantastic",
        "i am good","i am great","i am happy","i am wonderful","i am amazing",
        "i'm good","i'm great","i'm happy","i'm wonderful","i'm amazing","i'm doing well",
        "actually feeling good","actually feeling great","actually feeling happy",
        "feeling really good","feeling so good","feeling so happy","feeling so great",
        # Life achievement keywords — ALWAYS map to happy regardless of other words
        "got a job","secured a job","got the job","got selected","got accepted","got promoted",
        "passed my exam","passed my exams","passed the exam","cleared my exam","cleared the exam",
        "cleared","cracked","won","achieved","graduated","got admission","got offer",
        "offer letter","placed","placement","got into","got through","succeeded","success",
        "accomplished","milestone","dream come true","met","saw","visited","celebrated",
        "birthday","anniversary","married","engaged","baby","new home","moved in",
        # Short positive phrases
        "i passed","i won","i cleared","i cracked","i made it","i did it","i got in",
        "i got through","i got a","i secured","i achieved","i graduated",
    ],
    EmotionType.EXCITED: [
        "excited","excitement","can't wait","looking forward","pumped","hyped","thrilled",
        "energized","motivated","fired up","stoked","can't believe","unbelievable","incredible",
    ],
    EmotionType.CALM: [
        "calm","peaceful","relaxed","at ease","serene","tranquil","content","balanced",
        "centered","at peace",
    ],
}

MOOD_KEYWORDS = {
    MoodLevel.VERY_BAD: ["can't go on","want to die","end it","hopeless","no point","breaking down","crisis","emergency","help me","suicidal","worst day","falling apart","completely lost"],
    MoodLevel.BAD: ["bad","terrible","awful","horrible","not good","struggling","difficult","hard","rough","tough","miserable","suffering"],
    MoodLevel.GOOD: ["good","well","better","nice","positive","happy","great","glad","pleased"],
    MoodLevel.VERY_GOOD: ["amazing","fantastic","wonderful","excellent","best","perfect","incredible","outstanding","thriving","on top of the world","over the moon","ecstatic","overjoyed"],
}


def keyword_detect(text: str, prior_emotion: Optional[EmotionType] = None) -> dict:
    text_lower = text.lower()

    # ── Priority override: achievement phrases AND positive feeling phrases = happy ──
    ACHIEVEMENT_PHRASES = [
        # Achievement phrases
        "i passed", "i cleared", "i cracked", "i won", "i got a job", "i secured",
        "i graduated", "i achieved", "i got selected", "i got accepted", "i got promoted",
        "i got the job", "i got in", "i got through", "i made it", "i did it",
        "passed my exam", "passed my exams", "passed the exam", "cleared my exam",
        "cleared the exam", "got a job", "secured a job", "got selected", "got accepted",
        "got promoted", "got admission", "got offer", "offer letter",
        "happy that i", "happy because i", "happy i passed", "happy i got",
        # Positive feeling phrases — "feeling good/great/well" always = happy
        "feeling good", "feeling great", "feeling wonderful", "feeling amazing",
        "feeling happy", "feeling fantastic", "feeling awesome", "feeling blessed",
        "doing well", "doing great", "doing good", "doing amazing",
        "i'm good today", "i'm great today", "i'm happy today",
        "actually feeling good", "actually feeling great", "actually feeling happy",
        "feeling really good", "feeling so good", "feeling so happy",
        "i am actually", "actually good", "actually great", "actually happy",
    ]
    if any(phrase in text_lower for phrase in ACHIEVEMENT_PHRASES):
        # Determine mood level
        if any(kw in text_lower for kw in ["very happy", "so happy", "extremely happy", "overjoyed", "ecstatic"]):
            mood = MoodLevel.VERY_GOOD
        else:
            mood = MoodLevel.GOOD
        return {
            "emotion": EmotionType.HAPPY,
            "mood_level": mood,
            "confidence": 0.95,
            "reasoning": "Achievement phrase detected — always happy"
        }

    scores = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[emotion] = score

    if scores:
        detected_emotion = max(scores, key=scores.get)
    elif prior_emotion and prior_emotion != EmotionType.NEUTRAL:
        detected_emotion = prior_emotion
    else:
        detected_emotion = EmotionType.NEUTRAL

    mood_scores = {}
    for mood, keywords in MOOD_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            mood_scores[mood] = score

    if mood_scores:
        detected_mood = max(mood_scores, key=mood_scores.get)
    else:
        emotion_to_mood = {
            EmotionType.STRESSED: MoodLevel.BAD, EmotionType.ANXIOUS: MoodLevel.BAD,
            EmotionType.SAD: MoodLevel.BAD, EmotionType.ANGRY: MoodLevel.BAD,
            EmotionType.OVERWHELMED: MoodLevel.BAD, EmotionType.LONELY: MoodLevel.BAD,
            EmotionType.HAPPY: MoodLevel.GOOD, EmotionType.EXCITED: MoodLevel.GOOD,
            EmotionType.CALM: MoodLevel.NEUTRAL, EmotionType.NEUTRAL: MoodLevel.NEUTRAL,
        }
        detected_mood = emotion_to_mood.get(detected_emotion, MoodLevel.NEUTRAL)

    return {"emotion": detected_emotion, "mood_level": detected_mood, "confidence": 0.75, "reasoning": f"keyword:{detected_emotion.value}"}


MOOD_DETECTION_PROMPT = """You are an emotion detection system for a mental wellness app.
You receive conversation history plus the latest message. Detect the emotion of the LATEST message using context.

CRITICAL: If user previously expressed an emotion and their next message gives a REASON or SITUATION for it, keep the SAME emotion.
If user shares a positive life event (got a job, passed exam, won, met someone), detect as happy/excited.
If user shares a negative event (lost job, failed, broke up), detect as sad/stressed.
Only use neutral if there is genuinely no emotional signal AND no prior context.

Return ONLY valid JSON:
{"emotion": "<one of: stressed,anxious,sad,angry,happy,calm,overwhelmed,lonely,excited,neutral>",
 "mood_level": "<one of: very_bad,bad,neutral,good,very_good>",
 "confidence": <0.0-1.0>,
 "reasoning": "<one sentence>"}"""


def _extract_prior_emotion(conversation_history: list) -> Optional[EmotionType]:
    """
    Extract the most recent STRONG emotion from conversation history.
    Only used when the current message has NO clear emotion signal.
    Does NOT override when current message is clearly positive.
    """
    if not conversation_history:
        return None

    # Check last 4 user messages for any emotion signal
    for msg in reversed(conversation_history[-6:]):
        role = msg.role if hasattr(msg, 'role') else msg.get('role', '')
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        if role == "user":
            result = keyword_detect(content)
            if result["emotion"] != EmotionType.NEUTRAL:
                return result["emotion"]

    return None


async def detect_mood(
    user_message: str,
    conversation_history: list = None,
) -> dict:
    """
    Context-aware emotion and mood detection.
    Uses conversation history so follow-up messages stay in context.
    """
    if conversation_history is None:
        conversation_history = []

    prior_emotion = _extract_prior_emotion(conversation_history)

    # Keyword detection with prior context
    # IMPORTANT: Only pass prior_emotion if current message has NO strong signal
    # This prevents "I'm feeling good today" from being overridden by prior stressed context
    keyword_result = keyword_detect(user_message, prior_emotion)

    # If keyword detection found a POSITIVE signal, NEVER let prior negative override it
    POSITIVE_EMOTIONS = {EmotionType.HAPPY, EmotionType.EXCITED, EmotionType.CALM}
    if keyword_result["emotion"] in POSITIVE_EMOTIONS:
        # Current message is clearly positive — trust it, ignore prior negative context
        logger.info(f"Positive emotion detected: {keyword_result['emotion'].value} — ignoring prior context")
        prior_emotion = None  # don't let prior stressed/anxious override this

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Build context-aware messages
        api_messages = [{"role": "system", "content": MOOD_DETECTION_PROMPT}]

        # Include last 4 conversation turns for context
        for msg in conversation_history[-4:]:
            role = msg.role if hasattr(msg, 'role') else msg.get('role', 'user')
            content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
            api_messages.append({"role": role, "content": content})

        prior_str = prior_emotion.value if prior_emotion else "unknown"
        api_messages.append({
            "role": "user",
            "content": (
                f"Latest message: {user_message}\n\n"
                f"Prior emotional context from conversation: '{prior_str}'\n"
                f"Keyword analysis suggests: '{keyword_result['emotion'].value}'\n"
                f"Detect the emotion for the latest message using ALL this context."
            )
        })

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            temperature=0.1,
            max_tokens=150,
        )

        raw = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if not json_match:
            return keyword_result

        result = json.loads(json_match.group())
        emotion_str = str(result.get("emotion", "")).lower().strip()
        mood_str = str(result.get("mood_level", "")).lower().strip()

        try:
            emotion = EmotionType(emotion_str)
        except ValueError:
            emotion = keyword_result["emotion"]

        try:
            mood_level = MoodLevel(mood_str)
        except ValueError:
            mood_level = keyword_result["mood_level"]

        # If API returns neutral but keyword or prior context says otherwise, trust context
        if emotion == EmotionType.NEUTRAL:
            if keyword_result["emotion"] != EmotionType.NEUTRAL:
                logger.info(f"API returned neutral, using keyword result: {keyword_result['emotion'].value}")
                emotion = keyword_result["emotion"]
                mood_level = keyword_result["mood_level"]
            elif prior_emotion and prior_emotion != EmotionType.NEUTRAL:
                logger.info(f"API returned neutral, inheriting prior: {prior_emotion.value}")
                emotion = prior_emotion
                mood_level = keyword_result["mood_level"]

        final = {
            "emotion": emotion,
            "mood_level": mood_level,
            "confidence": float(result.get("confidence", 0.85)),
            "reasoning": result.get("reasoning", ""),
        }
        logger.info(f"Mood detected: {emotion.value}/{mood_level.value} for: '{user_message[:50]}'")
        return final

    except Exception as e:
        logger.error(f"Mood detector API error: {e} — using keyword fallback")
        return keyword_result
