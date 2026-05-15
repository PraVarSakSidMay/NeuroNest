"""
TTS Voice + Waterfall Test Script
===================================
Tests:
  1. API key presence for all providers
  2. Each of the 5 named voices (Amelia, Rachel, Josh, Nathan, Sam) via the normal waterfall
  3. Forced failover simulation — marks Tier 1 (ElevenLabs) as rate-limited, 
     confirms the next provider picks up automatically
  4. Full waterfall exhaustion — marks ALL providers as rate-limited,
     confirms None is returned (browser TTS fallback path)
"""

import sys, os, time
sys.path.insert(0, '.')

from core.config import settings
from services.tts_service import (
    generate_tts,
    _tts_rate_tracker,
    VOICE_MAPPING,
    tts_elevenlabs,
    tts_cartesia,
    tts_deepgram,
    tts_openai,
    tts_lmnt,
    tts_murf,
)

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results = []

def log(label, status, detail=""):
    icon = {"PASS": "[P]", "FAIL": "[F]", "SKIP": "[S]"}[status]
    line = f"  {icon} [{status}] {label}"
    if detail:
        line += f"  — {detail}"
    print(line)
    results.append((label, status, detail))


# ── 1. API Key Presence ─────────────────────────────────────────────────────
print("\n=== 1. API Key Presence ===")
key_map = {
    "ElevenLabs":  settings.ELEVENLABS_API_KEY,
    "Cartesia":    settings.CARTESIA_API_KEY,
    "Deepgram":    settings.DEEPGRAM_API_KEY,
    "OpenAI TTS":  settings.OPENAI_API_KEY,
    "LMNT":        settings.LMNT_API_KEY,
    "Murf":        settings.MURF_API_KEY,
}
for name, key in key_map.items():
    s = PASS if key else FAIL
    log(f"{name} key", s, key[:8] + "..." if key else "MISSING")


# ── 2. Test all 5 named voices via the normal waterfall ─────────────────────
print("\n=== 2. Named Voice Waterfall Test (all 5 voices) ===")
TEST_TEXT = "Hi, I'm your NeuroNest assistant. I'm here to support you today."
VOICES = list(VOICE_MAPPING.keys())  # ['Amelia', 'Rachel', 'Josh', 'Nathan', 'Sam']

for voice in VOICES:
    t0 = time.time()
    result = generate_tts(TEST_TEXT, "neutral", voice)
    elapsed = round(time.time() - t0, 2)
    if result and os.path.exists(result):
        size_kb = round(os.path.getsize(result) / 1024, 1)
        log(f"Voice: {voice}", PASS, f"file={os.path.basename(result)}, size={size_kb}KB, time={elapsed}s")
    else:
        log(f"Voice: {voice}", FAIL, f"returned None after {elapsed}s (browser TTS fallback will be used)")


# ── 3. Forced failover: mark ElevenLabs rate-limited, next tier must pick up ─
print("\n=== 3. Failover Test — ElevenLabs artificially rate-limited ===")
_tts_rate_tracker.mark_rate_limited("elevenlabs")
print("   [forced] ElevenLabs marked as rate-limited for 60s")

t0 = time.time()
result = generate_tts(TEST_TEXT, "neutral", "Rachel")
elapsed = round(time.time() - t0, 2)
if result and os.path.exists(result):
    log("Auto-switch after ElevenLabs limit", PASS, f"file={os.path.basename(result)}, time={elapsed}s")
else:
    log("Auto-switch after ElevenLabs limit", FAIL, "No provider succeeded")

# Clear cooldown so subsequent tests are not affected
_tts_rate_tracker.clear("elevenlabs")
print("   [cleared] ElevenLabs cooldown removed")


# ── 4. Forced failover: mark ALL providers rate-limited ──────────────────────
print("\n=== 4. Full Exhaustion Test — all providers rate-limited ===")
all_providers = ["elevenlabs", "cartesia", "deepgram", "openai_tts", "lmnt", "murf"]
for p in all_providers:
    _tts_rate_tracker.mark_rate_limited(p)
print("   [forced] All TTS providers marked as rate-limited")

result = generate_tts(TEST_TEXT, "neutral", "Rachel")
if result is None:
    log("Full exhaustion returns None (browser TTS fallback)", PASS, "frontend Web Speech API will handle it")
else:
    log("Full exhaustion should return None", FAIL, f"unexpected result: {result}")

# Restore all
for p in all_providers:
    _tts_rate_tracker.clear(p)
print("   [cleared] All cooldowns removed")


# ── Summary ──────────────────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
total   = len(results)
passed  = sum(1 for _, s, _ in results if s == PASS)
failed  = sum(1 for _, s, _ in results if s == FAIL)
skipped = sum(1 for _, s, _ in results if s == SKIP)
print(f"  Total:  {total}")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Skipped:{skipped}")
print()
if failed:
    print("  Failed tests:")
    for label, status, detail in results:
        if status == FAIL:
            print(f"    - {label}: {detail}")
