# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the backend of this repository. For full project overview including frontend, see the root [CLAUDE.md](../CLAUDE.md). Additional architectural conventions are documented in [.github/copilot-instructions.md](../.github/copilot-instructions.md).

## Common Commands

### Environment Setup (Ubuntu 24.04 / Python 3.10.13)
```bash
# Install dependencies with CPU-optimized llama-cpp-python (OpenBLAS)
CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install -r requirements.txt --timeout 300

# Or use the automated installation script
bash install_deps.sh
```

### Development Server
```bash
# Activate virtual environment (if not already)
source venv/bin/activate

# Run FastAPI server with auto-reload
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Start separate llama.cpp server for offline chat models (different process, port 8001)
# Note: The main server communicates with this offline LLM server via HTTP.
# Script not yet implemented; currently offline models are loaded directly.
```

### Testing
```bash
# Run ad‑hoc test scripts (no formal test framework)
cd src/test
python -m pytest  # if pytest installed, but currently not used
python OnlineLlm.py  # example manual test
```

### Environment Configuration
1. Copy `.env.example` to `.env` in the backend root.
2. Set `DEEPSEEK_API_KEY` for online LLM API access.
3. Other environment variables are loaded via `python-dotenv`.

### Model Management
- **Offline LLM models**: Place GGUF model files in `backend/model/`. Configure paths in `backend/src/config/general.py`.
  - Chat model: `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf`
  - Reasoning model: `Qwen3-4B-Thinking-2507-Q4_K_M.gguf`
- **Voice interaction models**: Sherpa‑onnx models go in `backend/src/voice_interaction/models/`. The `install_deps.sh` script can extract from tar archives.
- **Face recognition assets**: `backend/assets/face/face.png` is used for face recognition.
- **Map data**: `backend/assets/small1.map.json` contains navigation graph data.

## Architecture Overview

### Project Structure
```
backend/
├── src/
│   ├── config/          # Configuration constants (general.py)
│   ├── router/          # API routes (APIRouter pattern)
│   ├── smart_triager/   # Multi‑agent workflow for route patching
│   ├── llm/             # Online/offline LLM clients
│   ├── map/             # Navigation with Dijkstra pathfinding
│   ├── recorder/        # Face recognition and medical records
│   ├── IntegratedSystem/# Integrated face + medical record system
│   ├── voice_interaction/# Speech‑to‑text and text‑to‑speech
│   ├── medical/         # Medical‑specific agents
│   ├── logger.py        # Simple logging
│   └── utils.py         # Shared utilities
├── assets/              # Static assets (maps, face images)
├── docs/                # Design documentation
└── model/               # GGUF model files (not in version control)
```

### Core Design Principles

#### Single API Router
All routes are mounted under `/api` via `backend/src/router/__init__.py`. Feature‑specific routers are defined as `APIRouter(prefix="/feature")` and included in the main `api_router`.

#### Configuration Centralization
All constants and paths are defined in `backend/src/config/general.py` (e.g., `BACKEND_ROOT_DIR`, `OFFLINE_CHAT_MODEL_PATH`). Never hardcode paths; always import from this file.

#### LLM Agent Pattern
Each agent file follows a six‑layer structure (detailed in `backend/docs/llm_designing.md`):
1. **Imports + file comment** – docstring with file location and purpose.
2. **System prompt** (`instructions` variable) – sections: `## Background`, `## Role`, `## Input`, `## Output`, `## Criteria`, `## Requirements`, `## Example`.
3. **`logit_bias` config** – via `utils.build_logit_bias` to adjust token probabilities for small offline models.
4. **Async API functions** – `*_online()` and `*_offline()` variants.
5. **Raw output post‑processing** – parse LLM JSON output through Pydantic models.
6. **`__all__` export** – expose the public API.

#### Pydantic Everywhere
Request bodies, response data, LLM output schemas, and map structures all use Pydantic models. Typedef files (`*/typedef.py`) define shared models for a feature. Always validate LLM JSON output through a Pydantic model.

#### LLM Clients
- **Online**: DeepSeek via OpenAI‑compatible client (`llm/online/client.py`).
- **Offline**: llama‑cpp‑python (`llm/offline/`). Each agent exposes both variants; callers choose via `online_model: bool` parameter.

**Important concurrency note**: `llama-cpp-python` does not support concurrent calls on the same `Llama` instance. Shared instances must be called sequentially; different model instances (chat vs. reasoning) can run concurrently.

### Core Data Flows
1. **Smart Triage** (`/api/triager/get_route_patch/`): User text → `workflow.py` → Agent pipeline (condition_collector → requirement_collector → route_patcher) → patched route JSON.
2. **Face‑based Medical Records** (`recorder/recoder.py`): LLM tool‑calls → `IntegratedSystem` → `FaceRecognitionSystem` + `MedicalRecordSystem`.
3. **Navigation** (`map/tools.py`): `small1.map.json` loaded at module import time; Dijkstra pathfinding, tree translation for LLM consumption.

## Key Files to Read First

| File | Purpose |
|------|---------|
| `docs/backend_designing.md` | Routing patterns, config philosophy, overall file layout rules. |
| `docs/llm_designing.md` | Agent authoring standard, prompt structure, online/offline pattern. |
| `src/config/general.py` | All path/model constants (`BACKEND_ROOT_DIR`, `OFFLINE_CHAT_MODEL_PATH`, etc.). |
| `src/smart_triager/triager/workflow.py` | Reference implementation of a multi‑agent workflow. |
| `src/router/triager.py` | Reference implementation of a feature router. |
| `src/router/__init__.py` | Main API router mounting all sub‑routers under `/api`. |
| `src/llm/online/client.py` | DeepSeek online LLM client (OpenAI‑compatible). |
| `src/llm/offline/chat.py` | Offline chat model loader and inference wrapper. |
| `src/map/tools.py` | Navigation utilities with Dijkstra pathfinding. |
| `src/IntegratedSystem/integrated_system.py` | Integrated face recognition + medical record system. |

## Development Conventions

### Routing
- Simple routes go directly in `router/` (e.g., `router/triager.py`).
- Complex multi‑stage routes get a sub‑folder with an `__init__.py` defining a sub‑router (e.g., `router/navigator/`).
- Always use `APIRouter(prefix="/feature")` for feature routers.

### Testing
- No automated test framework. Ad‑hoc scripts live in `src/test/` (run directly with venv active).
- Route testing via Postman or browser.

### Startup Behavior
- `main.py` preloads the offline chat model on startup (`offline.get_offline_chat_model()`).
- Calls `remove_os_environ_proxies()` to prevent local API calls from being intercepted by system proxies.

### Code Style
- File header docstring: first line is a “URL” indicating file location, second line describes purpose.
- Imports: standard library imports first, then project imports, separated by a blank line.
- Two blank lines between import block and logic, and between functions/classes.
- Type hints encouraged, especially for LLM API functions.

## Important Constraints

1. **Offline LLM Context Limits**: `system prompt tokens + user input tokens + max_tokens` must not exceed `n_ctx` (Llama context window) to avoid segfault.
2. **Configuration References**: Always import paths/constants from `config/general.py`; never hardcode.
3. **Pydantic Validation**: Always validate LLM JSON output through Pydantic models.
4. **LLM Concurrency**: Do not make concurrent calls to the same llama‑cpp‑python `Llama` instance. Use sequential calls or separate instances.
5. **Voice Interaction**: Long‑press threshold is 250ms; visual feedback must be provided during recording (frontend concern but noted here).

## Troubleshooting

- **Numpy version conflicts**: MeloTTS may downgrade numpy, causing opencv incompatibility. The `install_deps.sh` script automatically fixes this by reinstalling numpy>=2.
- **Unidic dictionary issues**: If MeloTTS fails due to missing unidic, the script sets up a symlink from unidic_lite (included with MeloTTS) to the expected unidic directory.
- **Offline model segfaults**: Ensure total token count (system + user + max_tokens) does not exceed model's `n_ctx`. Check model context window size.
- **Face recognition failures**: Ensure `backend/assets/face/face.png` exists and is a valid image.
- **LLM concurrency errors**: Do not make concurrent calls to the same llama‑cpp‑python `Llama` instance. Use sequential calls or separate instances.

## Quick Reference

### Feature Router Example
```python
# router/triager.py
from fastapi import APIRouter
from src.smart_triager.triager.workflow import get_route_patch_workflow

triager_router = APIRouter(prefix="/triager")

@triager_router.get("/get_route_patch")
async def get_route_patch(text: str, online_model: bool = False):
    result = await get_route_patch_workflow(text, online_model=online_model)
    if result is None:
        return JSONResponse({"success": False}, status_code=500)
    return {"success": True, "data": result}
```

### LLM Agent API Example
```python
# Example from src/smart_triager/triager/requirement_collector.py
async def collect_requirement_online(input: str) -> RequirementCollectorOutput | None:
    agent = Agent(
        name="Requirement Collector",
        instructions=requirement_collector_instructions,
        model=online.get_model(),
        max_tokens=4096,
        logit_bias=_logit_bias
    )
    raw = await Runner.run(agent, input=input)
    # … parse raw JSON through Pydantic model
    return RequirementCollectorOutput.model_validate_json(raw)
```
