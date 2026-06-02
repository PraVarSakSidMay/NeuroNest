# PHASE 5: Clean Architecture Refactor (SOLID + Modularization)

**Status**: Architecture & Migration Plan

**Timeline**: 2–4 weeks (design + incremental implementation)

**Goal**: Transform the current monolith into a modular, testable, and production-ready codebase using Clean Architecture and SOLID principles. Preserve current features while making components swappable, observable, and easy to test.

---

## EXECUTIVE SUMMARY

This phase reorganizes the backend and frontend into clear layers, introduces dependency injection and adapter patterns, establishes well-defined interfaces, and adds test seams and CI checks. The refactor reduces coupling (especially around AI providers, Supabase, and TTS), improves testability, and makes it straightforward to scale horizontally.

Key outcomes:
- Domain logic separated from infrastructure
- Pluggable providers for LLMs, TTS, STT, and storage
- Unit-testable services without network calls
- Centralized error handling, logging, and metrics
- CI pipeline with unit, integration, and smoke tests

---

## ARCHITECTURAL PRINCIPLES

1. Single Responsibility: each module has one reason to change.
2. Dependency Inversion: high-level modules depend on abstractions, not concrete implementations.
3. Interface Segregation: small, purpose-specific interfaces.
4. Explicit Boundaries: adapters for external systems (Supabase, OpenAI, files).
5. Incremental Migration: break changes into safe, testable steps.

---

## TARGET LAYERS (CLEAN ARCHITECTURE)

1. Domain Layer (core):
   - Entities: Interaction, Session, User, AudioFeatures, EmotionData, Memory
   - Value Objects and Domain Exceptions
   - Pure business rules (e.g., contradiction detection, tone strategy)
   - No external dependencies

2. Application Layer (use-cases):
   - Orchestrates domain logic for use-cases (ProcessVoice, GenerateResponse, StoreInteraction, RetrieveMemories)
   - Defines interfaces (ports) required by domain (e.g., IAudioStore, IEmbeddingProvider, ILLMClient)
   - Input/Output DTOs

3. Interface / Adapter Layer (infrastructure):
   - Implementations of ports: SupabaseRepository, FileStorage, OpenAIClient, GroqClient, WhisperAdapter, TTSAdapter
   - HTTP controllers / FastAPI routes translate transport models to use-case input
   - Background workers, queue adapters

4. Framework Layer (delivery):
   - FastAPI app, routes, middleware (auth, CORS), logging, DI container bindings, Celery/RQ config
   - Frontend API proxies (Next.js server routes) if migrating frontend

---

## BINDING AND DEPENDENCY INJECTION

- Use a lightweight DI container (Python: `punq`, `wired`, or simple factory pattern). Keep it explicit in `main.py`.
- Bind at startup: map interfaces to concrete implementations using configuration.
- Example binding table:
  - IInteractionRepository -> SupabaseInteractionRepository
  - IEmbeddingProvider -> OpenAIEmbeddingProvider (or GroqEmbeddingProvider)
  - ILLMClient -> OpenAIClient or GroqClient
  - ITTSProvider -> ElevenLabsAdapter -> fallback chain via CompositeTTS
  - IAudioStorage -> LocalFileStorage or SupabaseStorageAdapter

---

## INTERFACES (PORTS) — KEY EXAMPLES

Create small interfaces (Python/Type hints) to decouple implementation:

```python
class IInteractionRepository(Protocol):
    async def create_user(self, full_name: str) -> str: ...
    async def create_session(self, user_id: str) -> Optional[str]: ...
    async def log_interaction(self, interaction: InteractionDTO) -> str: ...
    async def store_embedding(self, interaction_id: str, embedding: list[float]) -> bool: ...
    def get_supabase_client(self): ...
```

```python
class IEmbeddingProvider(Protocol):
    def generate_embedding(self, text: str) -> Optional[list[float]]: ...
```

```python
class ILLMClient(Protocol):
    async def chat(self, system_prompt: str, user_prompt: str, **opts) -> dict: ...
    async def generate_audio(self, text: str, voice: str) -> Optional[bytes]: ...
```

```python
class ITTSProvider(Protocol):
    async def synthesize(self, text: str, voice_name: str, metadata: dict) -> Optional[str]: ...
```

These small, well-documented interfaces are the contract between layers.

---

## ADAPTER PATTERNS

- Implement each external system as an adapter that implements a port.
- Example: `OpenAIAdapter` implements `ILLMClient`, `OpenAIEmbeddingProvider` implements `IEmbeddingProvider`.
- Create composite adapters for failover: `CompositeTTS` tries `ElevenLabsAdapter` -> `DeepgramAdapter` -> `WebTTSAdapter`.
- Adapters handle provider-specific errors and translate them into domain exceptions.

---

## BACKGROUND TASKS & QUEUES

- Move long-running or retryable work (embedding generation, large TTS generation, audio storage) to a background worker.
- Use Redis + RQ or Celery for queuing; tasks should rely on interface adapters, not concrete classes.
- Example tasks:
  - `store_embedding_task(interaction_id, text)` uses IEmbeddingProvider + IInteractionRepository
  - `generate_tts_task(interaction_id, response_text, voice)` uses ITTSProvider + IAudioStorage

---

## ERROR HANDLING, RETRIES & CIRCUIT BREAKERS

- Wrap external calls with retry + exponential backoff and circuit breaker (e.g., `tenacity`, `aiohttp` + custom logic).
- Adapters should raise domain-level exceptions (e.g., `ExternalServiceUnavailable`) not raw provider errors.
- Global error middleware captures exceptions and returns consistent API error responses.

---

## LOGGING & OBSERVABILITY

- Structured JSON logs. Use `structlog` or standard logging with JSON formatter.
- Capture context: request_id, session_id, user_id, model provider, latency.
- Instrument traces (OpenTelemetry) for distributed tracing across background tasks and API.
- Export metrics to Prometheus: request latency, TTS latency, embedding failures, model usage counts.

---

## SECURITY & CONFIGURATION

- Remove wildcard CORS; configure allowed origins via env.
- Secrets via environment variables or secret manager (GitHub Actions secrets, Azure Key Vault).
- Replace hardcoded user with real authentication (JWT, Supabase Auth or OAuth). Keep dev dummy but gated by feature flag.
- Ensure RLS correct in Supabase; adapter should pass a service role token for writes and user JWT for per-user operations.

---

## MIGRATION STRATEGY (INCREMENTAL)

Goal: avoid big-bang rewrite. Use strangler pattern.

1. Introduce interfaces and adapters without changing existing implementations. (1–2 days)
   - Add `ports.py` defining protocols.
   - Implement `adapters/` with thin wrappers that call current services but conform to interfaces.

2. Create `use_cases/` (Application layer) that call ports instead of direct services. (2–4 days)
   - Implement `process_voice_usecase.py` that orchestrates repository, model_manager, tts providers via interfaces.

3. Integrate DI container and bind current concrete implementations to interfaces. (1 day)
   - Add `container.py` with environment-driven bindings.

4. Replace direct imports in `main.py`/routes to call use-cases. (2–3 days)
   - Keep route signatures stable; refactor internals.

5. Background tasks: extract embedding storage and TTS generation to queue worker. (2–3 days)
   - Add `tasks.py` and simple Redis queue.

6. Add tests for use-cases and adapters using mocks. (ongoing)

7. Swap in new implementations gradually: e.g., replace OpenAI client with a new adapter and run integration tests. (2–5 days each swap)

8. Refactor frontend API calls if necessary; maintain backwards compatibility.

---

## TESTING & QUALITY GATES

- Unit tests for Domain & Application layers run on each PR.
- Adapter integration tests run in CI with test doubles for external services.
- Add contract tests for adapters to ensure they satisfy the ports.
- Add end-to-end smoke tests for critical flows: record -> process -> response -> play audio.
- Add static analysis: `ruff`/`flake8`, `mypy` strict typing for Python.

---

## CI/CD & Deployment

- GitHub Actions workflows:
  - `lint` (ruff/mypy)
  - `unit-tests` (pytest)
  - `integration-tests` (run with test Supabase instance using secrets)
  - `build-and-deploy` (build container, push to registry, deploy to staging)
- Dockerize backend; multi-stage build for smaller images.
- Use environment specific configuration: `dev`, `staging`, `production`.

---

## SAMPLE FILES TO ADD / MOVE

- backend/
  - domain/
    - entities.py (Interaction, AudioFeatures, EmotionData)
    - exceptions.py
  - application/
    - use_cases/
      - process_voice.py
      - generate_response.py
  - adapters/
    - storage/supabase_adapter.py
    - llm/openai_adapter.py
    - tts/elevenlabs_adapter.py
  - infra/
    - di.py
    - background/worker.py
  - controllers/
    - voice_controller.py (FastAPI routes wiring to use-cases)

---

## SAMPLE USE-CASE (PROCESS VOICE)

Pseudocode for `ProcessVoice` use-case:

```python
class ProcessVoice:
    def __init__(
        self, repo: IInteractionRepository, llm: ILLMClient,
        tts: ITTSProvider, embedding_provider: IEmbeddingProvider, logger
    ):
        self.repo = repo
        self.llm = llm
        self.tts = tts
        self.embedding = embedding_provider

    async def execute(self, session_id, user_id, audio_file, features):
        # 1. Transcribe (call STT adapter)
        transcript = await self.llm.transcribe(audio_file)

        # 2. Emotion detection (use emotion service via interface)
        emotion = await self._detect_emotion(transcript, features)

        # 3. Generate response via LLM use-case
        response = await self.llm.chat(system_prompt, transcript)

        # 4. Persist interaction
        interaction_id = await self.repo.log_interaction(InteractionDTO(...))

        # 5. Enqueue embedding generation
        queue.enqueue('store_embedding', interaction_id, transcript)

        # 6. Return stable DTO for API
        return ProcessVoiceResult(...)
```

---

## TIMELINE & ESTIMATES

- Phase 5 design & scaffolding: 2–4 days
- Implement ports & adapters (thin wrappers): 3–5 days
- Implement use-cases and DI container: 3–5 days
- Extract background tasks (queue + worker): 3–5 days
- Add tests & CI: 4–6 days
- Total: ~3–4 weeks depending on parallel work and review cycles

---

## RISK & MITIGATION

- Risk: Breaking existing API surface. Mitigation: keep controller endpoints stable; change internals only.
- Risk: Longer PRs. Mitigation: small, incremental PRs with feature flags.
- Risk: Test flakiness with external services. Mitigation: use test doubles; keep integration tests isolated.

---

## NEXT ACTIONS (I CAN DO NOW)

- Option A (Safe scaffolding): Create `ports.py`, `adapters/` wrappers, and `application/use_cases/process_voice.py` with tests. Bind adapters in `container.py` and switch `main.py` routes to use the use-case. (I recommend this first)

- Option B (Full refactor): Implement all layers and migrate services. Larger PRs, more risk.

Which option do you prefer? I can start by scaffolding Option A and open incremental PR-style patches here.