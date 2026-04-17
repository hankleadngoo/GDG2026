# Business Context — Resume Protector

## Problem

Recruiting teams face a contradictory pressure: process thousands of CVs quickly while maintaining high evaluation accuracy. Existing AI tools (ATS keyword matching, basic LLM summarizers) solve for speed but not depth — they cannot detect inflated credentials, surface hidden talent, or adapt to industry norms.

This creates a **dual failure mode**:
- Qualified candidates with poorly formatted CVs are silently rejected.
- Candidates who exaggerate credentials pass superficial screening.

## Solution

Resume Protector is a **Multi-Agent LLM system** that acts as an independent evaluation panel. It automates deep candidate assessment by combining:
1. Structured CV extraction
2. OSINT cross-verification against public profiles
3. Contradiction detection and trust scoring
4. Benchmarking against a historical corpus of real CVs
5. A synthesized, explainable hire/no-hire recommendation

The system is advisory — HR retains final decision authority (Human-in-the-loop).

---

## Target Users

### Primary — HR Departments & Tech Companies
- Automate bulk CV screening without sacrificing depth.
- Reduce time-to-shortlist; eliminate manual OSINT lookups.
- Get an objective benchmark: "how does this candidate compare to the market?"

### Secondary — Recruitment Platforms & Headhunters
- Validate large candidate databases at scale.
- Deliver pre-verified shortlists to enterprise clients, improving placement success rates.

### Indirect — Candidates
- Receive actionable feedback emails when their profile is incomplete or contradictory.
- Get a second chance to clarify and resubmit rather than being silently rejected.

---

## Competitive Advantages

| Capability | Traditional ATS | Generic AI Filters | Resume Protector |
|-----------|-----------------|-------------------|-----------------|
| Keyword matching | ✅ | ✅ | ✅ |
| Semantic understanding | ❌ | ✅ | ✅ |
| OSINT cross-verification | ❌ | ❌ | ✅ |
| Contradiction / fraud detection | ❌ | ❌ | ✅ |
| Industry benchmark (RAG) | ❌ | ❌ | ✅ |
| Candidate feedback email | ❌ | ❌ | ✅ |
| Self-learning from hiring outcomes | ❌ | ❌ | ✅ |
| Explainable, auditable output | ❌ | Partial | ✅ |

---

## MVP Scope (Hackathon)

Focus narrowed to the **IT industry** for the hackathon demo:
- Input: IT-domain CV (PDF)
- Benchmark corpus: `it-domain/` (649 IT CVs) + `data/all-domains/` (1 291 CVs)
- OSINT: LinkedIn + GitHub (most relevant for IT roles)
- Output: assessment report + hire recommendation visible in the HR dashboard

Explicitly **out of scope** for MVP:
- Video/audio interview analysis
- Multi-industry benchmarking (non-IT domains)
- Full enterprise security / data encryption compliance
- Production-scale load testing

---

## Self-Learning Loop

After each recruitment cycle closes, HR's final hire/reject decisions are fed back into the vector database. Future Agent 4 retrievals incorporate these outcomes as relevance signals, improving benchmark accuracy over time — without manual model retraining.

This creates a **compounding advantage**: the system becomes more accurate the longer it is used, unlike static ATS tools.

---

## Budget (Hackathon MVP)

| Resource | Approach | Cost |
|---------|---------|------|
| Cloud infrastructure | GCP Free Tier + student credits | ~$0 |
| LLM inference | Gemini API free tier (Google AI Studio) | ~$0 |
| Lightweight extraction | Gemma (local, open-source) | $0 |
| Vector DB | FAISS (local, open-source) | $0 |
| Agent framework | LangGraph / CrewAI (open-source) | $0 |
| OSINT APIs | Tavily / GitHub free tiers | ~$0 |
| Compute for testing | Google Colab / Kaggle free GPU | $0 |

**Total projected cost during hackathon: ~$0**

---

## Future Roadmap (Post-Hackathon)

1. **Multi-domain expansion** — extend benchmark corpus to Economics, Marketing, Healthcare.
2. **Multimodal interviews** — Speech-to-Text + facial expression analysis for live interview rounds.
3. **Enterprise compliance** — end-to-end data encryption, GDPR/PDPA compliance.
4. **API-as-a-Service** — expose Resume Protector as a REST API for ATS integrations.
5. **Knowledge graph layer** — infer latent skills from known technology relationships.
