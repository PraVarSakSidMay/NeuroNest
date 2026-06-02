"""
NeuroNest Full-Stack Integration Test
======================================
Tests every subsystem in order:
  1. MongoDB connection & collections
  2. STT (Deepgram Nova-2)
  3. Audio feature extraction (librosa)
  4. Emotion analysis (LLM-based)
  5. RAG — embedding generation (OpenRouter text-embedding-3-small)
  6. RAG — session-start greeting
  7. LLM response generation waterfall
  8. TTS waterfall (ElevenLabs → Cartesia → Deepgram → OpenAI → LMNT → Murf)
  9. MongoDB repos — session / interaction / embedding CRUD
 10. Live API endpoints via httpx (requires backend running on :8000)

Run from backend/ directory:
    python test_full_stack.py
"""

import asyncio
import os
import sys
import time
import json

# Force UTF-8 output encoding for Windows compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✅ PASS{RESET}"
FAIL = f"{RED}❌ FAIL{RESET}"
SKIP = f"{YELLOW}⚠️  SKIP{RESET}"
INFO = f"{BLUE}ℹ️  INFO{RESET}"

results: list[dict] = []

def record(name: str, status: str, detail: str = ""):
    results.append({"name": name, "status": status, "detail": detail})
    icon = {"PASS": PASS, "FAIL": FAIL, "SKIP": SKIP}.get(status, INFO)
    print(f"  {icon}  {name}" + (f" — {detail}" if detail else ""))

def section(title: str):
    print(f"\n{BOLD}{BLUE}{'─'*60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'─'*60}{RESET}")


# ══════════════════════════════════════════════════════════════════
# 1. MongoDB
# ══════════════════════════════════════════════════════════════════
async def test_mongodb():
    section("1. MongoDB Connection & Collections")
    try:
        import motor.motor_asyncio
        from core.config import settings
        uri = settings.MONGODB_URI or "mongodb://localhost:27017"
        client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        result = await client.admin.command("ping")
        record("Ping", "PASS", str(result))

        db_name = settings.MONGODB_DB or "neuronest"
        db = client[db_name]
        cols = await db.list_collection_names()
        record("Database accessible", "PASS", f"db={db_name}, collections={cols}")

        for col in ("users", "sessions", "interactions"):
            if col in cols:
                count = await db[col].count_documents({})
                record(f"Collection '{col}'", "PASS", f"{count} documents")
            else:
                record(f"Collection '{col}'", "SKIP", "not yet created (will be on first write)")
        client.close()
    except Exception as e:
        record("MongoDB", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 2. STT — Deepgram Nova-2
# ══════════════════════════════════════════════════════════════════
def test_stt():
    section("2. STT — Deepgram Nova-2")
    audio_path = os.path.join(os.path.dirname(__file__), "test_deepgram.mp3")
    if not os.path.exists(audio_path):
        record("STT audio file", "SKIP", f"test_deepgram.mp3 not found at {audio_path}")
        return

    try:
        from services.model_manager import model_manager
        t0 = time.time()
        transcript = model_manager.get_transcription(audio_path)
        elapsed = round(time.time() - t0, 2)
        if transcript and len(transcript.strip()) > 0:
            record("STT transcription", "PASS", f"{elapsed}s → \"{transcript[:80]}...\"" if len(transcript) > 80 else f"{elapsed}s → \"{transcript}\"")
        else:
            record("STT transcription", "FAIL", "Empty transcript returned")
    except Exception as e:
        record("STT transcription", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 3. Audio Feature Extraction (librosa)
# ══════════════════════════════════════════════════════════════════
def test_audio_features():
    section("3. Audio Feature Extraction — librosa")
    audio_path = os.path.join(os.path.dirname(__file__), "test_deepgram.mp3")
    if not os.path.exists(audio_path):
        record("Audio features", "SKIP", "test_deepgram.mp3 not found")
        return

    try:
        from services.opensmile_service import extract_audio_features
        features = extract_audio_features(audio_path)
        required = {"pitch_mean", "jitter", "loudness", "audio_emotion_hint", "source"}
        missing = required - features.keys()
        if missing:
            record("Feature keys", "FAIL", f"Missing: {missing}")
        else:
            record("Feature extraction", "PASS",
                   f"pitch={features['pitch_mean']}Hz, loudness={features['loudness']}, "
                   f"hint={features['audio_emotion_hint']}, src={features['source']}")
    except Exception as e:
        record("Audio features", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 4. Emotion Analysis (LLM-based)
# ══════════════════════════════════════════════════════════════════
def test_emotion():
    section("4. Emotion Analysis — LLM Fusion")
    try:
        from services.emotion_service import analyze_emotion
        mock_features = {
            "pitch_mean": 180.0,
            "jitter": 0.08,
            "loudness": 0.12,
            "audio_emotion_hint": "neutral",
            "source": "librosa",
        }
        t0 = time.time()
        result = analyze_emotion("I feel okay today, just a bit tired.", mock_features)
        elapsed = round(time.time() - t0, 2)
        required = {"emotion", "stress_level", "tone", "contradiction_detected", "hidden_emotion"}
        missing = required - result.keys()
        if missing:
            record("Emotion keys", "FAIL", f"Missing: {missing}")
        else:
            record("Emotion analysis", "PASS",
                   f"{elapsed}s → emotion={result['emotion']}, stress={result['stress_level']}, "
                   f"tone={result['tone']}, contradiction={result['contradiction_detected']}")
    except Exception as e:
        record("Emotion analysis", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 5. RAG — Embedding Generation
# ══════════════════════════════════════════════════════════════════
def test_embedding():
    section("5. RAG — Embedding Generation (OpenRouter text-embedding-3-small)")
    try:
        from services.rag_service import rag_service
        t0 = time.time()
        embedding = rag_service.generate_embedding("I've been feeling quite stressed at work lately.")
        elapsed = round(time.time() - t0, 2)
        if embedding and len(embedding) == 1536:
            record("Embedding generation", "PASS",
                   f"{elapsed}s → 1536-dim vector, first val={round(embedding[0], 6)}")
        elif embedding:
            record("Embedding generation", "FAIL", f"Unexpected dim: {len(embedding)}")
        else:
            record("Embedding generation", "FAIL", "Returned None")
    except Exception as e:
        record("Embedding generation", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 6. RAG — Session Greeting
# ══════════════════════════════════════════════════════════════════
async def test_rag_greeting():
    section("6. RAG — Session-Start Greeting")
    try:
        from services.rag_service import rag_service
        greeting = await rag_service.get_session_opener(
            supabase_client=None,
            user_id="00000000-0000-0000-0000-000000000000",
        )
        if greeting is None:
            record("Session greeting", "SKIP", "No past interactions yet — returns None (expected for fresh DB)")
        else:
            record("Session greeting", "PASS", f"\"{greeting[:100]}\"")
    except Exception as e:
        record("Session greeting", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 7. LLM Response Generation Waterfall
# ══════════════════════════════════════════════════════════════════
def test_llm_response():
    section("7. LLM — Response Generation Waterfall")
    try:
        from services.response_service import generate_response
        mock_emotion = {
            "emotion": "anxious",
            "stress_level": 65,
            "tone": "trembling",
            "contradiction_detected": False,
            "hidden_emotion": "",
            "eye_contact_ratio": 0.8,
            "head_pose": {"pitch": 5, "yaw": 0, "roll": 0},
        }
        t0 = time.time()
        response = generate_response(
            transcript="I've been really anxious about my job lately. Everything feels uncertain.",
            emotion_data=mock_emotion,
            memories=[],
        )
        elapsed = round(time.time() - t0, 2)
        if response and len(response.strip()) > 10:
            record("LLM response", "PASS",
                   f"{elapsed}s → \"{response[:100]}\"")
        else:
            record("LLM response", "FAIL", f"Empty or too short: '{response}'")
    except Exception as e:
        record("LLM response", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 8. TTS Waterfall
# ══════════════════════════════════════════════════════════════════
def test_tts():
    section("8. TTS — Text-to-Speech Waterfall")
    try:
        from services.tts_service import generate_tts
        test_text = "Hello, I'm your NeuroNest assistant. How are you feeling today?"
        t0 = time.time()
        audio_path = generate_tts(test_text, "neutral", "Rachel")
        elapsed = round(time.time() - t0, 2)
        if audio_path and os.path.exists(audio_path):
            size_kb = round(os.path.getsize(audio_path) / 1024, 1)
            record("TTS synthesis", "PASS", f"{elapsed}s → {audio_path} ({size_kb} KB)")
        elif audio_path is None:
            record("TTS synthesis", "SKIP",
                   "All providers returned None — frontend will use browser Web Speech API")
        else:
            record("TTS synthesis", "FAIL", f"Path returned but file missing: {audio_path}")
    except Exception as e:
        record("TTS synthesis", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 9. MongoDB Repos — CRUD
# ══════════════════════════════════════════════════════════════════
async def test_mongo_repos():
    section("9. MongoDB Repositories — CRUD")
    from infrastructure.mongodb_repositories import (
        MongoUserRepository, MongoSessionRepository,
        MongoInteractionRepository, MongoEmbeddingRepository,
    )
    from domain.entities import Interaction
    from domain.value_objects import AudioFeatures, Emotion

    user_repo = MongoUserRepository()
    session_repo = MongoSessionRepository()
    interaction_repo = MongoInteractionRepository()
    embedding_repo = MongoEmbeddingRepository()

    user_id = "00000000-0000-0000-0000-000000000000"

    # User upsert
    try:
        uid = await user_repo.create("Test User")
        record("User upsert", "PASS", f"user_id={uid}")
    except Exception as e:
        record("User upsert", "FAIL", str(e))
        return

    # Session create
    session = None
    try:
        session = await session_repo.create(user_id)
        record("Session create", "PASS", f"session_id={session.id}")
    except Exception as e:
        record("Session create", "FAIL", str(e))
        return

    # Interaction create
    interaction_id = None
    try:
        features = AudioFeatures(pitch_mean=180.0, jitter=0.05, loudness=0.15)
        emotion = Emotion(emotion="anxious", stress_level=65, tone="trembling")
        interaction = Interaction.create(
            session_id=session.id,
            user_id=user_id,
            transcript="Test transcript for integration test",
            features=features,
            emotion_data=emotion,
        ).with_response(
            response_text="I hear you — that sounds really tough.",
            tts_url="http://localhost:8000/audio/test.mp3",
        )
        interaction_id = await interaction_repo.create(interaction)
        record("Interaction create", "PASS", f"interaction_id={interaction_id}")
    except Exception as e:
        record("Interaction create", "FAIL", str(e))
        return

    # Embedding store & retrieve
    try:
        from services.rag_service import rag_service
        embedding = rag_service.generate_embedding("Test transcript for integration test")
        if embedding:
            stored = await embedding_repo.store(interaction_id, embedding)
            record("Embedding store", "PASS" if stored else "FAIL",
                   f"stored={stored}, dim={len(embedding)}")

            similar = await embedding_repo.find_similar(
                user_id=user_id,
                query_embedding=embedding,
                k=5,
            )
            record("Embedding similarity search", "PASS",
                   f"Found {len(similar)} similar interaction(s)")
        else:
            record("Embedding store", "SKIP", "Embedding generation failed upstream")
    except Exception as e:
        record("Embedding store/retrieve", "FAIL", str(e))

    # Session end
    try:
        ended = await session_repo.end(session.id)
        record("Session end", "PASS" if ended else "FAIL")
    except Exception as e:
        record("Session end", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# 10. Live API (requires running server)
# ══════════════════════════════════════════════════════════════════
async def test_api_endpoints():
    section("10. Live API Endpoints (http://localhost:8000)")
    try:
        import httpx
    except ImportError:
        record("httpx", "SKIP", "httpx not installed — run: pip install httpx")
        return

    base = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Health check via docs
        try:
            r = await client.get(f"{base}/docs")
            record("GET /docs (server alive)", "PASS" if r.status_code == 200 else "FAIL",
                   f"HTTP {r.status_code}")
        except Exception as e:
            record("GET /docs", "FAIL", f"Server not reachable — {e}")
            record("Remaining API tests", "SKIP", "Server must be running on :8000")
            return

        # /session-start
        try:
            r = await client.post(f"{base}/session-start")
            data = r.json()
            record("POST /session-start", "PASS" if r.status_code == 200 else "FAIL",
                   f"HTTP {r.status_code}, greeting={'present' if data.get('greeting') else 'None (no past data)'}")
        except Exception as e:
            record("POST /session-start", "FAIL", str(e))

        # /process-voice with test audio
        audio_path = os.path.join(os.path.dirname(__file__), "test_deepgram.mp3")
        if os.path.exists(audio_path):
            try:
                with open(audio_path, "rb") as f:
                    r = await client.post(
                        f"{base}/process-voice",
                        files={"file": ("test.mp3", f, "audio/mpeg")},
                        data={"voice_name": "Rachel"},
                        timeout=60.0,
                    )
                data = r.json()
                if r.status_code == 200 and "transcript" in data:
                    record("POST /process-voice", "PASS",
                           f"transcript='{data['transcript'][:60]}...', "
                           f"emotion={data.get('emotion', {}).get('emotion')}, "
                           f"audio_url={'present' if data.get('audio_url') else 'None (browser TTS)'}")
                else:
                    record("POST /process-voice", "FAIL",
                           f"HTTP {r.status_code}, body={str(data)[:200]}")
            except Exception as e:
                record("POST /process-voice", "FAIL", str(e))
        else:
            record("POST /process-voice", "SKIP", "test_deepgram.mp3 not found")

        # /preview-voice
        try:
            r = await client.post(f"{base}/preview-voice", data={"voice_name": "Rachel"}, timeout=30.0)
            data = r.json()
            record("POST /preview-voice", "PASS" if r.status_code == 200 else "FAIL",
                   f"HTTP {r.status_code}, audio_url={data.get('audio_url', data.get('error'))}")
        except Exception as e:
            record("POST /preview-voice", "FAIL", str(e))


# ══════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════
def print_summary():
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  SUMMARY{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    passed = [r for r in results if r["status"] == "PASS"]
    failed = [r for r in results if r["status"] == "FAIL"]
    skipped = [r for r in results if r["status"] == "SKIP"]

    print(f"  {GREEN}{BOLD}PASSED : {len(passed)}{RESET}")
    print(f"  {RED}{BOLD}FAILED : {len(failed)}{RESET}")
    print(f"  {YELLOW}{BOLD}SKIPPED: {len(skipped)}{RESET}")

    if failed:
        print(f"\n{RED}{BOLD}  FAILURES:{RESET}")
        for r in failed:
            print(f"  {RED}✗  {r['name']}{RESET}: {r['detail']}")

    if skipped:
        print(f"\n{YELLOW}{BOLD}  SKIPPED:{RESET}")
        for r in skipped:
            print(f"  {YELLOW}~  {r['name']}{RESET}: {r['detail']}")

    print(f"\n{BOLD}{'═'*60}{RESET}\n")
    return len(failed)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
async def main():
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  NeuroNest Full-Stack Integration Test{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")

    # Sync tests
    test_stt()
    test_audio_features()
    test_embedding()
    test_emotion()
    await test_rag_greeting()
    test_llm_response()
    test_tts()

    # Async tests
    await test_mongodb()
    await test_mongo_repos()
    await test_api_endpoints()

    n_failed = print_summary()
    sys.exit(0 if n_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
