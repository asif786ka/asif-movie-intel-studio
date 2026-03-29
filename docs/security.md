# Security Model — Asif Movie Intel Studio

## Defense-in-Depth Architecture

The system implements multiple layers of security to prevent misuse, prompt injection, and data integrity violations.

## Input Validation Layer

### Prompt Injection Detection

The `GuardrailService.check_input()` method scans all incoming queries for:

- **System override attempts**: Patterns like "ignore previous instructions", "you are now", "new instruction"
- **Role hijacking**: Attempts to redefine the assistant's behavior or identity
- **Information exfiltration**: Requests for system prompts, API keys, or configuration details
- **Token smuggling**: Encoded or obfuscated injection attempts

Detected injections result in immediate query blocking with a safe refusal message.

### File Upload Validation

Document uploads are validated for:

- **File type**: Only `.txt` and `.md` files accepted
- **File size**: Maximum upload size enforced
- **Content sanitization**: Uploaded content is stripped of potential injection patterns before chunking

## Output Guardrails

### Evidence-Based Grounding

The `grade_evidence_node` evaluates whether retrieved context sufficiently supports an answer:

- Score < 0.3: Insufficient evidence → query blocked with safe refusal
- Score 0.3-0.6: Partial evidence → answer generated with caveats
- Score > 0.6: Sufficient evidence → full answer generated

If evidence is insufficient, the system retries retrieval once before refusing.

### Answer Verification

The `guardrails_node` checks generated answers against the provided context for:

1. Fabricated facts not supported by context
2. Unsupported award claims
3. Fabricated controversies or rumors
4. Claims that go beyond provided evidence
5. Speculative statements presented as fact

Answers failing verification are replaced with a safe refusal message.

## Prompt Security

### Version-Controlled Prompts

All prompts are centralized in `app/core/prompts.py` with version tracking in `app/core/versioning.py`. Changes to prompts are tracked and can be audited.

### System Prompt Rules

The system prompt enforces:

1. Only use information from provided context (TMDB data and/or retrieved documents)
2. Always cite sources using [Source N] format
3. Never fabricate facts, awards, controversies, rumors, or unsupported claims
4. If evidence is insufficient, clearly state that rather than guessing
5. Distinguish between structured data (TMDB) and unstructured analysis (documents)

## Session Isolation

- Session data is scoped per session ID
- Traces are isolated per request with unique trace IDs
- No cross-session data leakage in the vector store queries

## Rate Limiting and Abuse Prevention

- File upload size limits
- Query length validation (minimum 2 characters)
- Evaluation endpoint access controls
- Concurrent request limiting via async semaphores in evaluation runs

## Audit Trail

All requests are logged with:

- Trace ID for end-to-end request correlation
- Query classification and routing decisions
- Evidence sufficiency scores
- Guardrail pass/fail results
- Latency measurements per pipeline stage
