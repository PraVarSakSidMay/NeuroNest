// Mock data used as fallback — do not delete

export const mockUser = {
  name: "Varsha Sharma",
  email: "varsha@example.com",
  avatar: "V",
  wellnessScore: 82,
  streak: 7,
  sleepAvg: 6.8,
  moodCheckins: 14,
};

export const mockMoodData = [
  { day: "Mon", score: 60 },
  { day: "Tue", score: 75 },
  { day: "Wed", score: 55 },
  { day: "Thu", score: 80 },
  { day: "Fri", score: 70 },
  { day: "Sat", score: 85 },
  { day: "Sun", score: 82 },
];

export const mockChatMessages = [
  { id: 1, role: "ai",   text: "Hello! I'm NeuroBot 🧠 How are you feeling today?", time: "10:00 AM" },
  { id: 2, role: "user", text: "I've been feeling a bit anxious lately.", time: "10:01 AM" },
  { id: 3, role: "ai",   text: "I hear you. Anxiety can feel overwhelming. Can you tell me more about what's been triggering it?", time: "10:01 AM" },
  { id: 4, role: "user", text: "Mostly work stress and not sleeping well.", time: "10:02 AM" },
  { id: 5, role: "ai",   text: "That's very common. Poor sleep and work stress often amplify each other. Let's try a quick breathing exercise — inhale for 4 counts, hold for 4, exhale for 6. Ready?", time: "10:02 AM" },
  { id: 6, role: "user", text: "Yes, let's try that.", time: "10:03 AM" },
  { id: 7, role: "ai",   text: "Great! 🌿 Breathe in... 1, 2, 3, 4. Hold... 1, 2, 3, 4. Breathe out slowly... 1, 2, 3, 4, 5, 6. How do you feel?", time: "10:03 AM" },
];

export const mockJournalEntries = [
  {
    id: 1,
    title: "Finding calm in chaos",
    content: "Today was overwhelming but I managed to take a 10-minute walk. It helped more than I expected. The fresh air cleared my head and I felt more grounded.",
    mood: "😌",
    moodLabel: "Calm",
    tags: ["anxiety", "self-care", "progress"],
    date: "May 13, 2026",
    time: "9:30 PM",
  },
  {
    id: 2,
    title: "Gratitude check",
    content: "Three things I'm grateful for today: my morning coffee, a kind message from a friend, and finishing a task I'd been avoiding for days.",
    mood: "😊",
    moodLabel: "Happy",
    tags: ["gratitude", "positivity"],
    date: "May 12, 2026",
    time: "8:15 PM",
  },
  {
    id: 3,
    title: "Rough day at work",
    content: "Presentation didn't go as planned. Feeling disappointed but trying to remind myself that one bad day doesn't define my worth.",
    mood: "😔",
    moodLabel: "Low",
    tags: ["work", "self-compassion"],
    date: "May 11, 2026",
    time: "10:45 PM",
  },
];
