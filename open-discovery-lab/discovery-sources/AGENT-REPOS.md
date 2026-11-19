# AGENT-REPOS — open-source repositories that turn an agent into a discovery engine

Companion to this registry (see `README.md`). Every repository below was
existence-verified against the GitHub API on 2026-11-15 (star counts
recorded at verification time). Sources: the owner's discovery-engine
research digest (2026-11-15) plus API checks; descriptions follow the
digest, corrected where the API disagreed.

The lab's working principle for all of them (**the "truth oracle" rule**):
an agent only makes net-new discoveries when a discovery loop is closed
against an external verifier — a simulator, a dataset, a strict
mathematical checker, or an instrument — so it can fail 1,000 times in
private before landing the 1 breakthrough that survives. This lab's grid
Ramsey pipeline (proven relaxation LB + re-counted witness = closed loop)
is exactly such an oracle; the repos below are general-purpose versions of
the same idea.

## 1. Plug-and-play skills (connect to an existing coding agent)

| repo | what it gives the agent | verified |
|---|---|---|
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 177 validated scientific skills; connects to 100+ databases across biology, chemistry, medicine, physics, engineering, Earth science; literature review, hypothesis generation, domain analysis. Install via the agent-skills standard (Claude Code, Cursor, Gemini CLI, Codex, OpenCode). 57,245 stars. | 2026-11-15 |
| [Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) | 98 modular skills across 23 categories covering the AI/ML research lifecycle: brainstorming, experiments, paper writing. 14,545 stars. | 2026-11-15 |
| [diptiman-mohanta/ResearchRadar](https://github.com/diptiman-mohanta/ResearchRadar) | Skills for research-gap finding and novelty auditing: peer-review analysis, unexplored-gap spotting, novel problem-statement generation. 1 star (early-stage). | 2026-11-15 |

## 2. Autonomous end-to-end discovery engines

| repo | what it does | verified |
|---|---|---|
| [SakanaAI/AI-Scientist-v2](https://github.com/SakanaAI/AI-Scientist-v2) | Fully autonomous ML experimentation: agentic tree search over hypotheses, writes and runs experiments, analyzes plots with a VLM, pivots on failure, drafts manuscripts. Needs Linux + NVIDIA GPU + Docker. 7,510 stars. | 2026-11-15 |
| [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw) | Idea-to-paper automation with human oversight: 23-stage pipeline, multi-source literature search (OpenAlex, Semantic Scholar, arXiv), 4-layer citation verification, multi-agent debate, hardware-aware sandbox experiments. 14,879 stars. | 2026-11-15 |
| [GAIR-NLP/SR-Scientist](https://github.com/GAIR-NLP/SR-Scientist) | Symbolic-regression scientist (ICLR 2026): analyzes raw data, tests candidate equations in a code sandbox, evolves hidden governing laws — net-new formulas from any dataset. 58 stars. | 2026-11-15 |

## 3. Cross-field synthesis and web research

| repo | what it does | verified |
|---|---|---|
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | Planner/execution agents recursively explore a topic across web + local documents; long citation-backed reports. 30,695 stars. | 2026-11-15 |
| [brycewang-stanford/lit-review-agent-tools](https://github.com/brycewang-stanford/lit-review-agent-tools) | Weekly-updated curated directory of 70+ agent tools for literature review: MCP servers, PDF parsers, systematic-review tooling — anti-hallucination citation workflows. 52 stars. | 2026-11-15 |

## 4. Discovery-loop engines (evolution / cross-field bridges)

| repo | what it does | verified |
|---|---|---|
| [algorithmicsuperintelligence/openevolve](https://github.com/algorithmicsuperintelligence/openevolve) | Open-source AlphaEvolve: evolutionary coding agent — mutates a starting algorithm against an automated scoring function across thousands of generations (faster matrix multiplication, better packing, tighter bounds). Needs a starting script + a score function. 7,779 stars. | 2026-11-15 |
| [lamm-mit/SciAgentsDiscovery](https://github.com/lamm-mit/SciAgentsDiscovery) | MIT's cross-field discovery system: ontological knowledge graphs over paper corpora; Ontologist/Scientist/Critic/Planner agent teams traverse unrelated-field bridges for novel hypotheses. (The owner's digest cited "lamm-mit/SciAgents", which 404s — this is the verified name.) 642 stars. | 2026-11-15 |

## How the lab uses these

- **Skills repos (1)** are the fastest upgrade path for the lab's own
  agent fleet — install, audit against Rule 0, and only then use.
- **Engines (2, 4)** map onto the lab's tracks: SR-Scientist ↔ Track D
  (math bounds from data), OpenEvolve ↔ Track A/D optimizers, SciAgents ↔
  the discovery engine's cross-field target queue.
- **Synthesis (3)** feeds the novelty audits required by Rule 0 before
  anything new is built.

Uniqueness note (Rule 0, checked 2026-11-15): this page is a verified,
lab-mapped pointer set — the underlying repos are prior art and are
attributed, not re-implemented. Searches recorded in `README.md`.
