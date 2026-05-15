# NeuroNest Frontend — Complete Technical Documentation

## Overview

The NeuroNest frontend is a **Next.js 16** application built with TypeScript and Tailwind CSS. It provides the chat UI, voice recording, text-to-speech, staggered animations, and an encrypted chat history viewer.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Framework** | Next.js | 16.2.6 | React framework with App Router, SSR, file-based routing |
| **Language** | TypeScript | 5.x | Type safety across all components |
| **Styling** | Tailwind CSS | 4.x | Utility-first CSS, dark theme |
| **State Management** | Zustand | 5.x | Lightweight global state for chat messages |
| **Icons** | Lucide React | 0.469+ | Icon library |
| **HTTP Client** | Native fetch | — | API calls to FastAPI backend |
| **Voice Input** | MediaRecorder API | Browser | Audio recording |
| **Voice Output** | Web Speech API | Browser | Text-to-speech (Google/Microsoft voices) |
| **Animations** | CSS keyframes | — | Typewriter effect, staggered card reveals |
| **Storage** | localStorage | Browser | Persistent anonymous user ID |

---

## Architecture

```
Browser
  │
  ▼
Next.js App Router (app/)
  │
  ├── / (page.tsx)          ← Main chat interface
  └── /history (page.tsx)   ← Encrypted chat history viewer
         │
         ▼
  Components (components/chat/)
         │
    ┌────┴────────────────────────────────────┐
    │                                         │
    ▼                                         ▼
ChatInput                              MessageBubble
  ├── VoiceRecorder                      ├── useTypewriter (word-by-word)
  ├── Quick prompts                      ├── TTSControls (auto-speak)
  └── sendChatMessage()                  ├── ProverbCard (staggered)
         │                               ├── SpecialActionCard (staggered)
         ▼                               ├── JokeCard (staggered)
  lib/api.ts                             ├── MusicCard (one-by-one)
  getOrCreateUserId()                    ├── CelebrationCard (positive mode)
         │                               ├── WellnessTip (staggered)
         ▼                               └── ActivityCard × 5 (one-by-one)
  FastAPI Backend
  (localhost:8000)
         │
         ▼
  store/chatStore.ts (Zustand)
  ├── messages[]
  ├── sessionId
  ├── isLoading
  ├── currentEmotion/Mood
  └── getHistory()
```

---

## File Structure — Every File Explained

```
frontend/
├── package.json                    # Dependencies and scripts
├── next.config.ts                  # Next.js configuration
├── tsconfig.json                   # TypeScript configuration
├── postcss.config.mjs              # PostCSS for Tailwind CSS
├── .env.local                      # NEXT_PUBLIC_API_URL=http://localhost:8000
│
├── app/
│   ├── globals.css                 # Global styles, Tailwind import, animations
│   ├── layout.tsx                  # Root layout with metadata
│   ├── page.tsx                    # Main chat page (/)
│   └── history/
│       └── page.tsx                # Chat history viewer (/history)
│
├── components/
│   └── chat/
│       ├── ChatInput.tsx           # Text input + quick prompts + voice button
│       ├── ChatWindow.tsx          # Message list + welcome screen
│       ├── MessageBubble.tsx       # Single message with all cards + animations
│       ├── VoiceRecorder.tsx       # Mic button → MediaRecorder → Whisper
│       ├── TTSControls.tsx         # Replay + ♀/♂ voice + 🔊 Auto toggle
│       ├── ActivityCard.tsx        # Single activity card (staggered reveal)
│       ├── MusicCard.tsx           # Music tracks with Spotify + YouTube (one-by-one)
│       ├── JokeCard.tsx            # Emotion-specific joke card
│       ├── ProverbCard.tsx         # Mental wellness scientist quote
│       ├── CelebrationCard.tsx     # Shown for happy/excited/calm (replaces activities)
│       ├── SpecialActionCard.tsx   # Breathing exercise card
│       └── MoodBadge.tsx           # Live emotion indicator in header
│
├── hooks/
│   ├── useTTS.ts                   # Text-to-speech hook (Google/Microsoft voices)
│   └── useTypewriter.ts            # Word-by-word text animation hook
│
├── store/
│   └── chatStore.ts                # Zustand global state for chat
│
└── lib/
    ├── api.ts                      # API client + getOrCreateUserId()
    └── utils.ts                    # Helpers: emoji maps, color maps, formatters
```

---

## Detailed File Descriptions

### `app/globals.css`
Global CSS file. Imports Tailwind CSS v4. Defines:
- CSS variables for background and foreground colors
- `.scrollbar-hide` utility class
- `@keyframes fadeIn` animation used by staggered card reveals
- `.animate-fade-in` class applied to each card as it appears

---

### `app/layout.tsx`
Root Next.js layout. Sets:
- Page title: "NeuroNest — AI Mental Wellness Companion"
- Meta description for SEO
- `antialiased` body class with dark background

---

### `app/page.tsx`
The main chat page at `/`. Contains:
- **Header**: NeuroNest logo, MoodBadge, History link, Clear chat button
- **Crisis Banner**: iCall and 988 hotline numbers (always visible)
- **ChatWindow**: Scrollable message list
- **ChatInput**: Text input at the bottom
- Background gradient blobs for visual depth

---

### `app/history/page.tsx`
Chat history viewer at `/history`. Features:
- **Auto-loads user ID** from localStorage via `getOrCreateUserId()`
- **View History tab**: Shows decrypted conversation in chat bubble format
- **Verify Encryption tab**: Shows ciphertext (what Supabase stores) vs plaintext (what user sees)
- Timestamps displayed in user's local timezone
- Encryption details panel explaining AES-256-GCM

---

### `components/chat/ChatInput.tsx`
The message input area at the bottom of the chat. Features:
- **5 quick prompt buttons**: Pre-written emotional starters
- **Auto-resizing textarea**: Enter to send, Shift+Enter for newline
- **VoiceRecorder**: Mic button for voice check-ins
- **Send button**: Disabled when empty or loading
- Captures conversation history BEFORE adding new message (prevents duplication)
- Calls `sendChatMessage()` with `user_id` for Supabase storage

---

### `components/chat/ChatWindow.tsx`
The scrollable message list. Features:
- **Welcome screen**: Shown when no messages exist — NeuroNest intro + emotion grid
- **Message list**: Renders `MessageBubble` for each message
- **Typing indicator**: Brain icon + "NeuroNest is thinking..." while loading
- Auto-scrolls to bottom on new messages

---

### `components/chat/MessageBubble.tsx`
The most complex component. Renders a single message with all its cards. Features:

**Typewriter effect**: Uses `useTypewriter` hook — text appears word by word at 45ms/word with blinking cursor.

**Auto-speak**: `useEffect` fires after typewriter finishes, calls `speak()` if autoSpeak is enabled.

**Staggered card reveal**: After text finishes, cards appear one by one:
- 300ms → ProverbCard
- 800ms → SpecialActionCard (breathing)
- 1300ms → JokeCard
- 1800ms → MusicCard
- 2300ms → WellnessTip
- 2800ms → Activities section

**Response mode logic**:
- `celebrate` / `reflect` (happy/excited/calm) → shows CelebrationCard, NO activities
- `support` (all other emotions) → shows full activity list

**Activity stagger**: Activities appear one by one every 500ms after text finishes.

---

### `components/chat/VoiceRecorder.tsx`
Handles audio recording and voice check-ins. Features:
- `getSupportedMimeType()` — tries formats in order: webm;codecs=opus → webm → ogg → mp4
- Records audio using `MediaRecorder` with 250ms data collection intervals
- Shows "Recording..." indicator while active
- Sends audio blob to `/api/voice/analyze`
- Displays transcribed text as user message

---

### `components/chat/TTSControls.tsx`
Text-to-speech control bar below each assistant message:
- **Replay button**: Re-reads the response
- **Stop button**: Stops current speech
- **♀ Female / ♂ Male toggle**: Switches voice gender
- **🔊 Auto / 🔇 Auto toggle**: Enables/disables auto-speak
- **Voice name display**: Shows current voice (e.g. "Google US English")

---

### `components/chat/ActivityCard.tsx`
Single activity card with staggered reveal. Props:
- `activity`: ActivitySuggestion object
- `index`: Position in list
- `visible`: Boolean controlled by parent — card only renders when true

Shows: emoji, title, category badge (color-coded), description, duration.

---

### `components/chat/MusicCard.tsx`
Music recommendations with staggered reveal. Features:
- Reveals tracks one by one every 600ms using `useEffect` + `setInterval`
- Shows bouncing dots while more tracks are loading
- Each track has: title, artist, reason, green Spotify button, red YouTube button

---

### `components/chat/JokeCard.tsx`
Yellow card showing an emotion-specific joke. Simple display component.

---

### `components/chat/ProverbCard.tsx`
Indigo card showing a quote from a mental wellness expert. Shows quote text and author name.

---

### `components/chat/CelebrationCard.tsx`
Shown for happy/excited/calm emotions INSTEAD of activities. Emotion-specific gradient:
- Happy → yellow/orange gradient with 🌟
- Excited → pink/purple gradient with 🚀
- Calm → teal/cyan gradient with 🌿

---

### `components/chat/SpecialActionCard.tsx`
Blue card for breathing exercises. Renders markdown-style bold text (`**text**`) as `<strong>` elements for proper formatting of breathing steps.

---

### `components/chat/MoodBadge.tsx`
Small pill in the header showing current detected emotion and mood level. Updates after each message. Uses emoji + color-coded text from `lib/utils.ts`.

---

### `hooks/useTTS.ts`
Text-to-speech hook with Google voice priority. Features:

**Voice priority order** (tries each in order):
1. Google US English (Chrome — best quality)
2. Google UK English Female/Male
3. Microsoft Aria/Jenny (Windows 11 natural voices)
4. Microsoft Zira/David (Windows 10)
5. Samantha/Karen (Apple/Mac)
6. Generic English fallback

**Rate/pitch tuning per voice type**:
- Google voices: rate 0.95, pitch 1.0
- Microsoft voices: rate 0.90, pitch 1.05
- Other voices: rate 0.92, pitch 1.1

**Global state**: `globalVoiceGender` and `globalAutoSpeak` are module-level variables so all instances share the same preference.

**Text cleaning**: Strips markdown (`**bold**`), emojis, and extra whitespace before speaking.

---

### `hooks/useTypewriter.ts`
Word-by-word text animation hook. Parameters:
- `text`: Full text to animate
- `speed`: Milliseconds between words (default 45ms)
- `enabled`: Whether to animate (false for user messages)

Returns `{ displayed, isDone }`. The `isDone` flag triggers auto-speak and card stagger.

---

### `store/chatStore.ts`
Zustand global state store. State:
- `messages`: Array of `DisplayMessage` (includes full `ChatResponse` for assistant messages)
- `sessionId`: Current session ID (null until first message)
- `isLoading`: Whether waiting for API response
- `isRecording`: Whether voice recording is active
- `currentEmotion` / `currentMood`: Latest detected emotion/mood for MoodBadge

Actions:
- `addUserMessage(content)`: Adds user message with UUID and timestamp
- `addAssistantMessage(content, response)`: Adds assistant message with full ChatResponse
- `getHistory()`: Returns `ChatMessage[]` for API (role + content only)
- `clearChat()`: Resets all state

---

### `lib/api.ts`
API client and user ID management.

**`getOrCreateUserId()`**: Creates a persistent anonymous UUID stored in `localStorage` under key `neuronest_user_id`. This ensures every conversation is saved to Supabase even without authentication. When your auth teammate integrates, replace this with the real user ID.

**`sendChatMessage(message, history, sessionId, userId)`**: Sends chat request to `/api/chat/`. Always includes `user_id` so data is saved to Supabase.

**`analyzeVoice(audioBlob, sessionId)`**: Sends audio to `/api/voice/analyze` with `user_id`.

---

### `lib/utils.ts`
Utility functions and lookup tables:
- `MOOD_EMOJI`: Maps mood levels to emojis (😔 😕 😐 🙂 😄)
- `MOOD_COLOR`: Maps mood levels to Tailwind color classes
- `EMOTION_EMOJI`: Maps emotions to emojis (😤 😰 😢 😠 😊 😌 🤯 🥺 🤩 😐)
- `CATEGORY_COLOR`: Maps activity categories to badge colors
- `formatMoodLabel()`: Converts "very_bad" → "Very Bad"
- `cn()`: Merges Tailwind classes using clsx + tailwind-merge

---

## State Flow

```
User types message
       │
       ▼
ChatInput.handleSend()
  1. getHistory() — capture BEFORE adding new message
  2. addUserMessage(text) — add to store
  3. sendChatMessage(text, history, sessionId, userId)
       │
       ▼
  FastAPI returns ChatResponse
       │
       ▼
  addAssistantMessage(response.response, response)
  setCurrentMood(emotion, mood)
  setSessionId(response.session_id)
       │
       ▼
  MessageBubble renders
  useTypewriter animates text word by word
  useEffect fires after isDone → speak() if autoSpeak
  useEffect fires after isDone → stagger cards with timeouts
  useEffect fires after isDone → stagger activities with interval
```

---

## Response Modes

The `response_mode` field in `ChatResponse` controls what the frontend shows:

| Mode | Triggered by | What appears |
|------|-------------|--------------|
| `support` | stressed, anxious, sad, angry, overwhelmed, lonely, neutral | Proverb → Breathing → Joke → Music → Tip → 5 Activities |
| `celebrate` | happy, excited | Proverb → Celebration card → Music → Joke |
| `reflect` | calm | Proverb → Reflection card → Music → Joke |

---

## Environment Variables

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Quick Start

```cmd
cd frontend
npm install
npm run dev
```

Frontend: **http://localhost:3000**
History page: **http://localhost:3000/history**
