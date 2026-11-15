# competitions-benchmarks — 28 sources

| source | what you can do there | agent access | tier | url check |
|---|---|---|---|---|
| [Advent of Code](https://adventofcode.com) | Annual 25-problem puzzle series with verifiable answers — agent oracle practice. | Answer checker per puzzle. | curated | ok |
| [AIcrowd](https://www.aicrowd.com) | Research-flavored AI challenges (RL, agents, NLP). | CLI + Docker submissions. | curated | ok |
| [ARC Prize](https://arcprize.org) | Abstraction-and-reasoning-corpus benchmark/competition for ARC-AGI-2 with public leaderboard and $1M prizes. | Download ARC task JSONs from the GitHub repos and evaluate solvers locally. | curated | 200 |
| [BigCodeBench](https://bigcode-bench.github.io) | Practical code generation benchmark. | HF dataset + harness. | curated | ok |
| [BigCodeBench](https://github.com/bigcode-project/bigcodebench) | Practical coding benchmark with 1,140 task-oriented problems requiring diverse library calls. | Run the eval harness (pip install bigcodebench) with sandboxed execution. | curated | 200 |
| [Chatbot Arena (LMArena)](https://lmarena.ai) | Human-vote LLM leaderboard — live model-quality oracle. | Public leaderboard data. | curated | 403-bot |
| [CodaBench](https://www.codabench.org) | Open competition platform (NeurIPS/ICML tracks). | API. | curated | ok |
| [Codeforces](https://codeforces.com) | Large competitive-programming site with problem archives, ratings and contest history. | Use the public Codeforces API (codeforces.com/api) for problems, submissions and ratings. | curated | 403-bot |
| [CTFtime (CTF events)](https://ctftime.org) | Global calendar/rankings of capture-the-flag security competitions with writeup links. | Use the CTFtime API (ctftime.org/api/v1) for events and team rankings. | curated | 403-bot |
| [DrivenData](https://www.drivendata.org) | Data-science competitions for social impact. | CLI/API. | curated | ok |
| [EvalPlus](https://github.com/evalplus/evalplus) | Rigorous code-generation benchmark (HumanEval+, MBPP+) with 80x more tests to catch wrong solutions. | Run evalplus.evaluate with generated code files for pass@k scoring. | curated | 200 |
| [GAIA](https://huggingface.co/spaces/gaia-benchmark/leaderboard) | General-agent assistant benchmark (web/tools). | HF dataset + leaderboard. | curated | ok |
| [GAIA benchmark](https://huggingface.co/datasets/gaia-benchmark/GAIA) | Meta benchmark of 466 real-world questions requiring web browsing, tool use and reasoning for agents. | Load via datasets lib (gated; accept terms) and evaluate agent answers against the reference files. | curated | 200 |
| [HELM](https://crfm.stanford.edu/helm) | Stanford holistic LLM evaluation suite. | Leaderboard + harness. | curated | ok |
| [ICFP Contest](https://www.icfpcontest.org) | Annual programming contest (since 2000) with novel problem types. | Browse. | curated | ok |
| [Kaggle competitions](https://www.kaggle.com/competitions) | Live ML competitions with leaderboards and prize pools. | kaggle CLI. | curated | ok |
| [LiveBench](https://livebench.ai) | Contamination-free LLM benchmark with monthly refreshed questions across math, coding, reasoning. | Fetch leaderboard JSONs from livebench.ai or its GitHub results repo. | curated | 200 |
| [LiveCodeBench](https://livecodebench.github.io) | Contamination-free code benchmark (rolling problems). | Public harness. | curated | ok |
| [MLE-bench](https://github.com/openai/mle-bench) | OpenAI benchmark evaluating agents on 75 Kaggle ML-engineering competitions end-to-end. | Run the mle-bench harness (Docker-based) to score agents on Kaggle tasks. | curated | 200 |
| [MLPerf](https://mlcommons.org) | Industry-standard benchmark suites (Training/Inference/HPC) with published results across hardware. | Download reference implementations and result tables from mlcommons.org/benchmarks. | curated | 200 |
| [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | Massive Text Embedding Benchmark leaderboard comparing embedding models across 50+ tasks. | Pull per-model results from the mteb/results GitHub/HF repos. | curated | 200 |
| [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard) | HF's open-model evaluation leaderboard. | HF space + results dataset. | curated | ok |
| [OSWorld](https://os-world.github.io) | OS-level agent benchmark across real desktop apps. | Harness + VMs. | curated | ok |
| [Rosalind](https://rosalind.info) | Bioinformatics problem platform: 300+ algorithmic biology puzzles with dataset downloads per problem. | Fetch problem datasets via its URL endpoints and verify solutions on the site. | curated | 200 |
| [SWE-bench](https://www.swebench.com) | Real-GitHub-issue resolution benchmark — the coding-agent oracle. | Docker harness + public dataset. | curated | ok |
| [Terminal-Bench](https://www.tbench.ai) | Benchmark measuring agents on end-to-end terminal tasks inside Docker with programmatic checkers. | Run the tb CLI harness with your agent against the task suite containers. | curated | 200 |
| [WebArena](https://webarena.dev) | Realistic web-agent environments (self-hosted sites). | Docker harness. | curated | ok |
| [Zindi](https://www.zindi.africa) | Africa-focused data-science competition platform with regional prediction challenges. | Register free to access competition datasets and leaderboards. | curated | redirect-ok |
