# Future Roadmap: NeuroNest Evolution

This document outlines the scope for implementing advanced AI features in NeuroNest, focusing on long-term memory, autonomous actions, and standardized data interaction.

## 1. RAG (Retrieval-Augmented Generation)

Currently, NeuroNest has a short-term memory limited by the session. Implementing RAG will allow the assistant to remember past interactions across weeks or months.

### Scope:
- **Vector Database**: Use Supabase's `pgvector` to store embeddings of past conversation transcripts.
- **Context Retrieval**: Before generating a response, the system will search for similar past conversations.
- **Personalized Insights**: "I remember you were feeling anxious about your exam last Tuesday. How did it go?"
- **Emotional Trends**: Analyze longitudinal emotional data to identify triggers or progress.

### Implementation:
1. Generate embeddings using OpenAI's `text-embedding-3-small` or a local model.
2. Store in a `vector` column in the `interactions` table.
3. Use a similarity search (cosine similarity) during the `generate_response` phase.

## 2. AI Agents

Moving from a reactive assistant to a proactive agent that can perform tasks.

### Scope:
- **Tool Calling**: Give the LLM access to tools like `send_email`, `schedule_reminder`, `get_weather`, or `log_wellness_metric`.
- **Autonomous Follow-ups**: If a user is highly distressed, the agent could automatically schedule a check-in for the next morning.
- **Multimodal Agency**: Analyze not just voice, but also heart rate data (if integrated) or calendar events.

### Implementation:
1. Use OpenAI's Function Calling or Groq's Tool Use capabilities.
2. Define a set of "Wellness Tools" that the model can invoke based on the conversation flow.

## 3. MCP (Model Context Protocol)

MCP is a standard for how AI models interact with data sources and tools.

### Scope:
- **Local Data Access**: Safely allow the AI to read local files (e.g., a wellness journal) or local database states using standardized MCP servers.
- **Interoperability**: Easily switch between different model providers (Anthropic, OpenAI, Google) while maintaining the same tool-use and data-access patterns.
- **Standardized Connectors**: Connect NeuroNest to external wellness APIs (Oura, Apple Health, Fitbit) using MCP-compliant interfaces.

### Implementation:
1. Implement an MCP server that exposes NeuroNest's emotional history database.
2. Use an MCP-compatible client to orchestrate the models and their access to these resources.

---

## Conclusion
By combining **RAG** for memory, **Agents** for action, and **MCP** for interoperability, NeuroNest can transition from a simple voice interface to a comprehensive, deeply personalized wellness companion.
