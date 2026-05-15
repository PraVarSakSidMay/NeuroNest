"""Activity generator — emotion-specific, no activities for happy/excited/calm."""
import random
from typing import List
from app.models.schemas import EmotionType, MoodLevel, ActivitySuggestion

NO_ACTIVITY_EMOTIONS = {EmotionType.HAPPY, EmotionType.EXCITED, EmotionType.CALM}

ACTIVITY_BANK = {
    EmotionType.STRESSED: [
        ActivitySuggestion(title="Brain Dump — Get It Out of Your Head", description="Write every single stressor without filtering. Once it's on paper, your brain stops trying to hold it all. Then circle just ONE thing to handle today.", duration="10 minutes", category="mindfulness", emoji="📝"),
        ActivitySuggestion(title="4-7-8 Breathing — Your Stress Off Switch", description="Inhale for 4 counts, hold for 7, exhale for 8. Repeat 4 times. This directly activates your parasympathetic nervous system — the biological off switch for stress.", duration="5 minutes", category="breathing", emoji="🌬️"),
        ActivitySuggestion(title="Walk Away — Literally", description="Leave whatever is stressing you and walk outside for 10 minutes. Don't think about the problem. Physical distance from the stressor creates mental distance too.", duration="10 minutes", category="movement", emoji="🚶"),
        ActivitySuggestion(title="Cancel or Delay One Thing Today", description="Stress often comes from overcommitting. Look at your list and find ONE thing you can cancel, delay, or hand off. Protecting your time and energy is not selfish — it's survival.", duration="5 minutes", category="mindfulness", emoji="🚫"),
        ActivitySuggestion(title="Cold Water Face Splash", description="Splash cold water on your face 3 times. This triggers the mammalian dive reflex and immediately lowers your heart rate.", duration="2 minutes", category="movement", emoji="💧"),
        ActivitySuggestion(title="Call Someone and Just Say It", description="Call or text one person and say 'I'm really stressed right now.' Just saying it out loud to someone who cares cuts the mental weight in half.", duration="10 minutes", category="social", emoji="📞"),
        ActivitySuggestion(title="Progressive Muscle Release", description="Starting from your toes, tense each muscle group for 5 seconds then release. Work up to your shoulders. You're carrying stress in your body — this physically releases it.", duration="10 minutes", category="movement", emoji="💪"),
    ],
    EmotionType.ANXIOUS: [
        ActivitySuggestion(title="5-4-3-2-1 Grounding — Right Now", description="Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste. This pulls your brain out of the imagined future and into the safe present moment.", duration="5 minutes", category="mindfulness", emoji="🌿"),
        ActivitySuggestion(title="Write the Worry — Then Fact-Check It", description="Write exactly what you're anxious about. Then write: 'What is the realistic probability this actually happens?' Most anxious thoughts collapse under examination.", duration="8 minutes", category="creative", emoji="📓"),
        ActivitySuggestion(title="Box Breathing — 6 Rounds", description="In for 4, hold for 4, out for 4, hold for 4. Repeat 6 times. Used by Navy SEALs before high-pressure situations.", duration="5 minutes", category="breathing", emoji="📦"),
        ActivitySuggestion(title="Shake Your Body for 60 Seconds", description="Stand up and shake your hands, arms, and whole body for 60 seconds. Animals do this after a threat to discharge nervous energy.", duration="2 minutes", category="movement", emoji="🕺"),
        ActivitySuggestion(title="Phone Down for 30 Minutes", description="Anxiety feeds on information overload. Put your phone face down and step away from news and social media for 30 minutes.", duration="30 minutes", category="mindfulness", emoji="📵"),
        ActivitySuggestion(title="What Can I Control Right Now?", description="Draw two columns: 'In my control' and 'Not in my control.' List every worry. Then focus ONLY on the left column.", duration="7 minutes", category="creative", emoji="✍️"),
        ActivitySuggestion(title="Hold Something Cold or Warm", description="Hold an ice cube or a warm mug of tea. The intense physical sensation interrupts the anxiety loop and brings you back into your body.", duration="3 minutes", category="mindfulness", emoji="🧊"),
    ],
    EmotionType.SAD: [
        ActivitySuggestion(title="Let Yourself Feel It Fully", description="Put on music that matches your sadness and just sit with it for 10 minutes. Sadness that's allowed to exist passes faster than sadness that's suppressed.", duration="10 minutes", category="mindfulness", emoji="💧"),
        ActivitySuggestion(title="Send One Message — Even Just 'Hey'", description="Text one person you trust. 'Hey, having a rough day' is enough. Human connection is the fastest antidote to sadness.", duration="5 minutes", category="social", emoji="💬"),
        ActivitySuggestion(title="Write to Yourself Like a Friend", description="Write a letter to yourself the way you'd write to a close friend who was sad. You deserve that same warmth and compassion.", duration="10 minutes", category="creative", emoji="💌"),
        ActivitySuggestion(title="Child's Pose — Release the Weight", description="Get on the floor in child's pose and stay there for 3 minutes, breathing slowly. This releases emotional tension stored in your hips and lower back.", duration="10 minutes", category="movement", emoji="🧘‍♀️"),
        ActivitySuggestion(title="Find 3 Things That Were Okay Today", description="Not 'good' things — just things that were okay. 'I had a warm drink.' Small things count. This gently widens your lens.", duration="5 minutes", category="mindfulness", emoji="🙏"),
        ActivitySuggestion(title="Watch Something Comforting", description="Put on a show or movie that feels like comfort food — familiar, warm, low-stakes. Sometimes your mind just needs a break.", duration="30 minutes", category="creative", emoji="📺"),
        ActivitySuggestion(title="Cry It Out — Completely", description="If you feel like crying, let yourself cry fully. Crying releases stress hormones and genuinely makes you feel lighter afterward.", duration="10 minutes", category="mindfulness", emoji="😢"),
    ],
    EmotionType.ANGRY: [
        ActivitySuggestion(title="Burn Off the Adrenaline — Move Hard", description="Do 30 jumping jacks, run in place, or punch a pillow hard. Anger floods your body with adrenaline — physical movement is the only way to metabolize it.", duration="5 minutes", category="movement", emoji="🏃"),
        ActivitySuggestion(title="Write the Anger Letter — Then Destroy It", description="Write everything you're angry about, completely unfiltered. Then tear it up or delete it. Release without real-world consequences.", duration="10 minutes", category="creative", emoji="✉️"),
        ActivitySuggestion(title="Long Exhale Breathing", description="Breathe in for 4 counts, exhale slowly for 8 counts. The extended exhale activates your parasympathetic system and physically lowers your blood pressure.", duration="5 minutes", category="breathing", emoji="😮‍💨"),
        ActivitySuggestion(title="10-Minute Rule Before Responding", description="If you want to say or do something right now, set a 10-minute timer first. Most anger-driven decisions look completely different after 10 minutes of space.", duration="10 minutes", category="mindfulness", emoji="⏱️"),
        ActivitySuggestion(title="Peaceful Music — Don't Fight the Anger", description="Put on slow, calming instrumental music. Don't try to stop being angry — just let the music exist alongside the feeling.", duration="10 minutes", category="creative", emoji="🎶"),
        ActivitySuggestion(title="What's Really Underneath the Anger?", description="Anger is almost always a secondary emotion covering hurt, fear, or feeling disrespected. Write: 'I'm angry because...' then 'And underneath that, I actually feel...'", duration="8 minutes", category="mindfulness", emoji="🔍"),
        ActivitySuggestion(title="Ice Cube in Your Hand", description="Hold an ice cube tightly. The intense cold sensation overrides the anger signal in your brain and gives you a moment of reset.", duration="2 minutes", category="mindfulness", emoji="🧊"),
    ],
    EmotionType.OVERWHELMED: [
        ActivitySuggestion(title="Do Just ONE 2-Minute Task", description="Pick the absolute smallest task — reply to one message, wash one cup. Completing even one tiny thing breaks the paralysis of overwhelm.", duration="5 minutes", category="mindfulness", emoji="✅"),
        ActivitySuggestion(title="Brain Dump — Then Pick Just One", description="Write every single thing overwhelming you. Then circle ONE thing that matters today. Draw a line through everything else.", duration="10 minutes", category="creative", emoji="🗂️"),
        ActivitySuggestion(title="Step Away for 15 Minutes — Completely", description="Walk away from everything for 15 minutes. Go outside, lie down, do nothing. Your brain needs a circuit breaker.", duration="15 minutes", category="movement", emoji="🚪"),
        ActivitySuggestion(title="Ask for Help with One Thing", description="Identify one thing someone else could help with and actually ask them. Overwhelm almost always comes from trying to carry everything alone.", duration="5 minutes", category="social", emoji="🤝"),
        ActivitySuggestion(title="Emergency Breathing Reset", description="Inhale 4 counts, hold 7, exhale 8. Do this 4 times. When you're overwhelmed, your breathing is shallow and fast — this resets your nervous system.", duration="4 minutes", category="breathing", emoji="🌬️"),
        ActivitySuggestion(title="Lower the Bar — Just for Today", description="What's the minimum acceptable version of what you need to do today? Do that. Done is better than perfect when you're overwhelmed.", duration="5 minutes", category="mindfulness", emoji="📉"),
        ActivitySuggestion(title="Body Scan — Where Are You Holding It?", description="Close your eyes and slowly scan from head to toe. Where are you holding tension? Breathe into those spots and consciously release them.", duration="8 minutes", category="mindfulness", emoji="🔍"),
    ],
    EmotionType.LONELY: [
        ActivitySuggestion(title="Go Somewhere with People Around You", description="Go to a café, library, park, or any public space. You don't have to talk to anyone. Just being physically near other humans reduces loneliness significantly.", duration="30 minutes", category="social", emoji="🏙️"),
        ActivitySuggestion(title="Start One Small Conversation Today", description="Say something to someone — a cashier, a neighbor, a classmate. 'Nice weather' counts. Small interactions build social confidence.", duration="5 minutes", category="social", emoji="💬"),
        ActivitySuggestion(title="Reach Out to Someone You've Lost Touch With", description="Think of one person you used to be close to. Send them a message — 'Hey, I was thinking about you.' Most people are genuinely happy to hear from old friends.", duration="5 minutes", category="social", emoji="📱"),
        ActivitySuggestion(title="Join a Community Around Something You Love", description="Find a Reddit community, Discord server, local club, or online group around any interest you have. Shared interest is one of the fastest ways to build real connection.", duration="20 minutes", category="social", emoji="🌐"),
        ActivitySuggestion(title="Do One Thing Outside Your Comfort Zone", description="Attend an event, try a class, or introduce yourself to someone new. One small brave step is all it takes to start changing things.", duration="60 minutes", category="movement", emoji="💪"),
        ActivitySuggestion(title="Write About the Connection You Want", description="Describe the kind of friendships and relationships you want in your life. Be specific and honest. Clarity about what you want is the first step to building it.", duration="10 minutes", category="creative", emoji="✍️"),
        ActivitySuggestion(title="Volunteer or Help Someone Today", description="Find a local volunteer opportunity or simply help someone today. Giving to others is one of the most powerful ways to feel connected and less alone.", duration="60 minutes", category="social", emoji="🤲"),
    ],
    EmotionType.NEUTRAL: [
        ActivitySuggestion(title="Honest Check-In With Yourself", description="Sit quietly for 5 minutes and ask: how am I really feeling underneath 'fine'? Sometimes neutral is a cover for something deeper.", duration="5 minutes", category="mindfulness", emoji="🔍"),
        ActivitySuggestion(title="Do One Thing You Actually Enjoy", description="Pick one thing you genuinely like doing — not productive, just enjoyable. Neutral days are perfect for reconnecting with what brings you joy.", duration="20 minutes", category="creative", emoji="🎮"),
        ActivitySuggestion(title="Move Your Body — Even a Little", description="A 10-minute walk, some stretching, or a quick workout. Physical movement is one of the most reliable mood-shifters there is.", duration="10 minutes", category="movement", emoji="🏃"),
        ActivitySuggestion(title="Reach Out to Someone Just to Chat", description="Send a message to a friend or family member just to connect. Sometimes a neutral mood just needs a little human warmth.", duration="15 minutes", category="social", emoji="💬"),
        ActivitySuggestion(title="Try One Small New Thing", description="Do one small thing you've never done before — a new recipe, a new route, a new song. Novelty is a natural mood elevator.", duration="15 minutes", category="creative", emoji="✨"),
        ActivitySuggestion(title="Write 5 Specific Things You're Grateful For", description="Not generic — specific. 'The coffee I had this morning' counts. Specificity makes gratitude real and shifts your brain chemistry.", duration="5 minutes", category="mindfulness", emoji="🙏"),
    ],
    EmotionType.HAPPY: [],
    EmotionType.EXCITED: [],
    EmotionType.CALM: [],
}

WELLNESS_TIPS = {
    MoodLevel.VERY_BAD: "You're going through something really hard right now. Please remember — it's okay to ask for help. If you're in crisis, reach out to iCall: 9152987821 (India) or 988 (US). You don't have to face this alone.",
    MoodLevel.BAD: "Difficult days are part of life, not a sign that something is permanently wrong. Be gentle with yourself today. Small steps count more than you think.",
    MoodLevel.NEUTRAL: "Neutral days are actually great opportunities. Your mind is clear — use it to build a small positive habit, rest, or reconnect with something you enjoy.",
    MoodLevel.GOOD: "You're in a good place today. Use this energy to do something meaningful, connect with someone you care about, or simply appreciate how you feel right now.",
    MoodLevel.VERY_GOOD: "You're thriving! This is a great time to reflect on what's working well and think about how you can sustain this positive momentum.",
}


def get_activities(emotion: EmotionType, mood_level: MoodLevel, count: int = 5) -> List[ActivitySuggestion]:
    if emotion in NO_ACTIVITY_EMOTIONS:
        return []
    activities = ACTIVITY_BANK.get(emotion, ACTIVITY_BANK[EmotionType.NEUTRAL])
    if mood_level == MoodLevel.VERY_BAD:
        emergency = ActivitySuggestion(title="Start Here — Emergency Calm Breathing", description="Place one hand on your chest, one on your belly. Breathe in slowly for 5 counts, out for 7. Repeat 5 times. Do this before anything else — it will help.", duration="3 minutes", category="breathing", emoji="🫁")
        rest = list(activities)
        random.shuffle(rest)
        return [emergency] + rest[:count - 1]
    shuffled = list(activities)
    random.shuffle(shuffled)
    return shuffled[:count]


def get_wellness_tip(mood_level: MoodLevel) -> str:
    return WELLNESS_TIPS.get(mood_level, WELLNESS_TIPS[MoodLevel.NEUTRAL])
