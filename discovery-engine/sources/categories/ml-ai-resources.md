# ml-ai-resources — 52 sources

| source | what you can do there | agent access | tier | url check |
|---|---|---|---|---|
| [AI2 OLMo](https://github.com/allenai/OLMo) | Fully open LLM family (7B/13B/32B) releasing weights, data, code and training logs. | Download checkpoints and training data from HF allenai org for open-model experiments. | curated | 200 |
| [Aider](https://aider.chat) | Terminal coding agent with repo-map + git integration. | Local install. | curated | ok |
| [Artificial Analysis](https://artificialanalysis.ai) | Independent LLM speed/quality/cost benchmarks. | Browse. | curated | ok |
| [AutoGen](https://microsoft.github.io/autogen) | Microsoft multi-agent framework (research-grade). | Local install. | curated | ok |
| [bioRxiv](https://www.biorxiv.org) | Biology preprints (fresh findings before journals). | API (bioRxiv API). | curated | ok |
| [CORE](https://core.ac.uk) | Open-access research aggregator (300M+ hosted/downloaded). | API (free key). | curated | ok |
| [CrewAI](https://docs.crewai.com) | Role-based multi-agent framework. | Local install. | curated | ok |
| [Crossref](https://www.crossref.org) | DOI metadata + citation counts for 150M+ works. | REST API. | curated | ok |
| [CVAT](https://www.cvat.ai) | Intel-originated open computer-vision annotation tool supporting boxes, polygons, masks and video tracking - widely used for CV dataset curation. | REST API + SDK; serverless agent hooks for model-assisted annotation. | curated | ok |
| [Dask](https://www.dask.org) | Parallel Python for larger-than-memory dataframes/arrays with dashboard - the scaling companion to pandas/numpy. | Python API + distributed scheduler; per-collection docs. | curated | ok |
| [DOAJ](https://doaj.org) | 20k+ open-access journals (1M+ OA articles). | API. | curated | 403-bot |
| [Dolma (AI2 pretraining corpus)](https://huggingface.co/datasets/allenai/dolma) | 3-trillion-token open pretraining corpus with source-tagged subsets (C4, Wikipedia, PeS2o...). | Download token/stream shards from HF for pretraining or filtering experiments. | curated | 200 |
| [DSPy (Stanford NLP)](https://github.com/stanfordnlp/dspy) | Programming framework optimizing LM prompts/pipelines declaratively with teleprompters. | Pip-install dspy and compile programs against any LM API for tuned pipelines. | curated | 200 |
| [DVC](https://dvc.org) | Data & model versioning tool built on Git - manages large ML datasets/checkpoints with remotes (S3, GCS) and pipelines. | CLI + Python API; cache/remotes documented; works alongside GitOps flows. | curated | ok |
| [EleutherAI](https://www.eleuther.ai) | Open research collective behind GPT-Neo/Pythia, the Pile and lm-evaluation-harness - the volunteer community that open-sourced frontier-scale work. | Model weights on HuggingFace; evaluation harness on GitHub with task YAML registry. | curated | redirect-ok |
| [EleutherAI lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | Standard framework evaluating LLMs on 300+ tasks with standardized prompts and metrics. | Run lm_eval CLI against HuggingFace or API-backed models for reproducible scores. | curated | 200 |
| [Epoch AI](https://epoch.ai) | Research org tracking AI compute, model performance trends and benchmark data with open databases. | Download their machine-learning-benchmark and frontier-model databases (CSV) from epoch.ai/data. | curated | 200 |
| [FineWeb (HF)](https://huggingface.co/datasets/HuggingFaceFW/fineweb) | 15-trillion-token clean web corpus from CommonCrawl with dedup and filtering benchmarks. | Pull parquet shards via HF hub for LLM pretraining data pipelines. | curated | 200 |
| [Gradio](https://www.gradio.app) | Hugging Face's quick-UI library for ML demos (inputs/outputs to web app in lines) - standard for model sharing and HF Spaces. | Python SDK; `gradio deploy` integrations; REST-able endpoints from interfaces. | curated | ok |
| [Hugging Face Hub](https://huggingface.co) | Central hub for 1.5M+ models, 500k+ datasets and spaces with per-file download and discussion history. | Use the HF Hub Python library / REST API (huggingface.co/api) to search, download and upload artifacts. | curated | 200 |
| [Hugging Face models](https://huggingface.co/models) | 1M+ open models with inference APIs and spaces. | transformers/REST inference endpoints. | curated | ok |
| [Hugging Face Spaces](https://huggingface.co/spaces) | Community-hosted ML demos/apps (Gradio, Streamlit, Docker) usable as live tools and reference implementations. | Interact with Gradio/Streamlit Spaces via their REST APIs or embed them as agent tools. | curated | 200 |
| [Keras](https://keras.io) | High-level deep-learning API (now multi-backend: TF/JAX/PyTorch) - the gentlest path to model prototyping. | Python API; per-backend guides; KerasCV/KerasNLP models. | curated | ok |
| [Label Studio](https://labelstud.io) | Open-source data-annotation platform (images, audio, text, video) with ML-assisted pre-labeling - the standard self-hosted labeling tool. | REST API for projects/tasks/annotations; SDK for automated labeling pipelines. | curated | ok |
| [LAION-5B](https://huggingface.co/datasets/laion/laion2B-en) | 5.85B CLIP-filtered image-text links for training text-to-image models (Laion aesthetic subsets). | Download the metadata parquet shards; fetch images from original URLs as needed. | curated | 200 |
| [LangGraph](https://langchain-ai.github.io/langgraph) | Graph-based agent orchestration. | Local install. | curated | ok |
| [Lightning AI](https://www.lightning.ai) | PyTorch Lightning + Lightning AI studio: training-loop framework removing boilerplate with reproducible configs. | Python API; per-module docs; cloud studios freemium. | curated | ok |
| [LlamaIndex Docs](https://docs.llamaindex.ai) | Framework docs for building RAG/LLM applications with connectors to 100+ data sources. | Scrape the docs (also mirrored on GitHub) for integration recipes when building pipelines. | curated | redirect-ok |
| [LM Studio hub](https://lmstudio.ai) | Local LLM runtime with OpenAI-compatible server. | Local REST. | curated | ok |
| [medRxiv](https://www.medrxiv.org) | Health-sciences preprints. | API. | curated | 403-bot |
| [MLflow](https://mlflow.org) | Open-source experiment tracking and model registry (now with tracing for LLMs) - the de facto MLOps backbone for reproducible runs. | Python/REST APIs; `mlflow.start_run` pattern; artifact stores pluggable. | curated | ok |
| [ModelScope](https://www.modelscope.cn) | Alibaba's open model hub (15M+ downloads/day): 10k+ models and datasets with strong Chinese-language coverage. | Python SDK (modelscope) plus REST endpoints for model/dataset discovery. | curated | ok |
| [NLTK](https://www.nltk.org) | The classic NLP teaching toolkit with 50+ corpora and lexical resources (WordNet) bundled - foundational for text-processing education. | `nltk.download` corpora; Python API; book online with exercises. | curated | ok |
| [Ollama library](https://ollama.com/library) | Run open models locally with one command. | Local REST (11434). | curated | ok |
| [ONNX](https://onnx.ai) | Open standard for ML model interchange (operators, graph format) enabling cross-framework deployment - key for portable model artifacts. | Format spec, IR definitions and reference runtime (onnxruntime) documented. | curated | ok |
| [ONNX Model Zoo](https://github.com/onnx/models) | Collection of ready-to-run pretrained models in ONNX format (vision, text, speech). | Download .onnx weights directly for local inference experiments. | curated | 200 |
| [OpenAlex](https://openalex.org) | Fully open scholarly graph (successor to Scopus): 250M+ works. | REST API + snapshot bulk. | curated | ok |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | Autonomous software-development agent (formerly OpenDevin). | Local install + sandbox. | curated | ok |
| [OpenML](https://www.openml.org) | Open platform of 5,000+ datasets and millions of ML tasks/runs with results for reproducibility. | Use the OpenML REST API (openml.org/api/v1) or python openml client for task search. | curated | 200 |
| [OpenRouter](https://openrouter.ai) | Unified API to 300+ LLMs incl. free tiers — agent fuel. | OpenAI-compatible REST. | curated | ok |
| [Papers with Code](https://paperswithcode.com) | Papers + code + SOTA tables per task — find what is unsolved. | REST API. | curated | ok |
| [Polars](https://pola.rs) | Rust-based fast DataFrame library (lazy evaluation, multi-threaded) - the modern pandas alternative for data pipelines. | Python/Node/Rust APIs; user guide per feature. | curated | ok |
| [PyTorch](https://pytorch.org) | Dominant deep-learning framework (define-by-run tensors, autograd) with ecosystem (torchvision, torchaudio) powering most modern research. | Python API; TorchScript/C++ deployment; per-release docs and tutorials. | curated | ok |
| [Ray](https://www.ray.io) | Distributed-compute framework (Anyscale) unifying training (Train), tuning (Tune), serving (Serve) and RLlib - the scaling layer for ML work. | Python API; cluster launcher CLI; per-library docs. | curated | ok |
| [Roboflow Universe](https://universe.roboflow.com) | Community CV dataset hub: 200k+ annotated object-detection/segmentation datasets. | Register free and pull datasets via the Roboflow SDK/REST API. | curated | 403-bot |
| [Semantic Scholar](https://www.semanticscholar.org) | 220M+ papers with citation graphs and TLDRs. | Graph API (free key) + bulk. | curated | ok |
| [spaCy](https://spacy.io) | Industrial-strength NLP pipeline library (tokenization, NER, transformers integration) with reproducible config system. | Python API; pre-trained models downloadable per language; config YAML standard. | curated | ok |
| [State of AI Report](https://www.stateof.ai) | Annual research/industry/policy synthesis with cited data on compute, funding and capability trends - a curated annual snapshot for orientation. | Report PDF and referenced datasets published each October; links crawlable. | curated | ok |
| [Streamlit](https://streamlit.io) | Python-to-app framework for data dashboards and ML tools - the fastest path from script to shareable web interface. | Python SDK; component API; cloud deploy via CLI. | curated | ok |
| [TensorFlow](https://www.tensorflow.org) | Google's end-to-end ML platform (Keras API) with production deployment paths (TFLite, TF Serving) and TFX pipelines. | Python API; per-version docs; model hub integration (TF Hub). | curated | ok |
| [UC Irvine Machine Learning Repository](https://archive.ics.uci.edu) | Classic ML dataset repository (600+ datasets) used for benchmarks since the 1980s. | Download datasets via dataset-ID URL patterns (archive.ics.uci.edu/dataset/N). | curated | 200 |
| [Unpaywall](https://unpaywall.org) | Legal OA version finder for any DOI. | REST API. | curated | ok |
