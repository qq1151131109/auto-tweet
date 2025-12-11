# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a standalone high-concurrency NSFW tweet generation system that **completely decouples from ComfyUI** while **preserving all fine-tuned prompts and logic** from the original ComfyUI workflow. It directly calls LLM APIs using async Python to generate AI persona content.

**Core Design**: The system retains ComfyUI-based prompt engineering and generation logic while replacing the ComfyUI execution layer with direct async LLM API calls, achieving 5-10x performance improvement through native concurrency.

**Critical**: All prompts, calendar generation logic, and content strategies are **copied verbatim** from the original ComfyUI nodes. Do NOT modify these fine-tuned prompts without understanding their purpose.

**Recent Major Features** (as of Dec 2025):
- **Content Pool System (DEFAULT)**: Generate tweets by content type distribution without needing calendar ⭐ NEW
- **LLM Realism Injection**: Real-world photography effects (blur, grain, lighting flaws) injected via LLM
- **Mirror Selfie Optimization**: 25-30% mirror selfie content for higher engagement
- **PromptEnhancer System**: Decoupled architecture for model-specific prompt enhancement (Z-Image/SDXL)
- **FastAPI REST API**: Production-ready API with Celery background workers
- **Dual Configuration System**: `generation_config.yaml` (LLM params) + `image_generation.yaml` (image model params)

## Quick Start Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# For image generation with LoRA support (optional)
pip install git+https://github.com/huggingface/diffusers

# Download Z-Image model (30GB, for image generation)
python download_zimage_model.py

# Configure API keys
cp .env.example .env
# Edit .env with your API credentials
```

### Testing
```bash
# Run full test suite
cd tests && bash test.sh

# Test Z-Image environment (no model loading)
python tests/test_zimage.py

# Test LLM realism injection
python test_llm_realism.py

# Test prompt enhancer
python test_prompt_enhancer.py

# Test tweet length validation
python test_tweet_length.py

# Note: Tests expect files at ../personas/*.json and ../calendars/*.json
```

### API Server (Production Mode)
```bash
# Start Redis (required for Celery)
# macOS: brew services start redis
# Linux: sudo systemctl start redis
# Docker: docker run -d -p 6379:6379 redis:7-alpine

# Start API server + Celery workers
bash start_api.sh

# API will be available at:
# - Swagger docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/health
# - Celery Flower (optional): http://localhost:5555
```

### Complete Workflow

**1. Generate persona from image:**
```bash
python main.py \
  --generate-persona \
  --image character.png \
  --persona-output personas/my_character.json \
  --api-key "xxx"
```

**2. Generate tweets (Content Pool Mode - ⭐ NEW DEFAULT):**
```bash
# Generate by content type distribution (no calendar needed)
python main.py \
  --persona personas/my_character.json \
  --tweets 10 \
  --api-key "xxx"
```

**2b. Generate tweets (Calendar Mode - Traditional):**
```bash
# Generate by date (requires calendar, use --use-calendar flag)
python main.py \
  --persona personas/my_character.json \
  --calendar calendars/my_character.json \
  --tweets 10 \
  --use-calendar \
  --enable-context \
  --api-key "xxx"
```

**3. Generate images (multi-GPU):**
```bash
python main.py \
  --generate-images \
  --tweets-batch output_standalone/my_character_*.json \
  --num-gpus 4
```

### Batch Mode (High Concurrency)
```bash
python main.py \
  --batch-mode \
  --personas personas/*.json \
  --calendars calendars/*.json \
  --tweets 10 \
  --max-concurrent 20
```

## Architecture

### Critical Design Patterns

**1. Async Concurrency Model**
- Uses `asyncio.gather()` for true parallelism
- `LLMClientPool.semaphore` limits concurrent API calls (default: 20)
- Each persona generation is an independent async task
- Failures captured via `return_exceptions=True`

**2. Multi-Stage Persona Generation (7 stages)**
Location: `core/persona_generator.py`

The persona generation is a **sequential pipeline** that MUST complete in order:
1. Core persona (vision model analyzes image → base persona)
2. Tweet strategy (content_type_distribution)
3. Example tweets (8 high-quality examples)
4. Social network (friends, relationships)
5. Realism system (typos, flaws, authentic patterns)
6. Visual archive (outfits, poses, lighting preferences)
7. Knowledge base (character_book entries)

**DO NOT** modify this pipeline without understanding the dependencies between stages.

**3. LLM Realism Injection System** ⭐ NEW
Location: `docs/LLM_REALISM_INJECTION.md`

Real-world photography effects are injected through LLM guidance, NOT post-processing:
- System prompt contains categorized realism tokens (lighting flaws, motion blur, grain, etc.)
- LLM intelligently selects 2-4 modifiers based on scene context
- Scene-aware selection: "messy background" for outdoor, "low lighting" for night scenes
- Appended to `scene_hint` by LLM: "Morning in bedroom... Raw photo, candid photography, messy background, uneven skin tone"

**Critical**: This approach is superior to PromptEnhancer for flexibility. LLM understands context (e.g., doesn't add "motion blur" to still poses).

**4. PromptEnhancer System** (Legacy/Alternative)
Location: `core/prompt_enhancer.py`, `config/image_generation.yaml`

Decoupled architecture for model-specific prompt enhancement:
- Separates semantic `scene_hint` (LLM output) from technical `positive_prompt` (model input)
- Model-specific: Z-Image (realism tokens) vs SDXL (photography quality tokens)
- 3-level realism: LOW (minimal), MEDIUM (balanced), HIGH (maximum authenticity)
- Can be disabled via `image_generation.yaml` to use pure LLM realism injection

**5. Dual Configuration System** ⭐ NEW
- `generation_config.yaml`: LLM generation params (temperature, max_tokens, persona stages)
- `image_generation.yaml`: Image model params (realism level, steps, CFG, GPU settings)
- Both use YAML for easy editing without code changes

**6. Context Flow**
```
main.gather_context()
  → BatchTweetGenerator.generate_batch(context=xxx)
    → StandaloneTweetGenerator.generate_single_tweet(context=xxx)
```

Context includes date/weather and is injected into tweet generation prompts.

**7. Multi-GPU Image Generation**
Location: `core/image_generator.py`

Uses `torch.multiprocessing` with process pools:
- Single GPU: Sequential generation
- Multi-GPU: Task queue distributes to different GPUs, result queue collects outputs
- LoRA support via Diffusers mode (auto-load/unload to avoid contamination)

### Key Files and Their Roles

**core/prompt_enhancer.py** ⭐ NEW (Model-specific prompt enhancement)
- `PromptEnhancer`: Base class for adding model-specific tokens
- `ZImageEnhancer`: Z-Image-specific realism tokens
- `SDXLEnhancer`: SDXL-specific photography quality tokens
- `enhance_prompt()`: Convenience function
- `create_prompt_enhancer()`: Factory function

**config/image_config.py** ⭐ NEW (Configuration management)
- Loads `image_generation.yaml`
- `get_enhancer_from_config()`: Creates PromptEnhancer from YAML settings
- Preset system: "high_quality", "balanced", "authentic", "sdxl"

**config/image_generation.yaml** ⭐ NEW (Image generation settings)
- Model selection (Z-Image/SDXL)
- Realism level (low/medium/high)
- Generation params (steps, CFG, dimensions)
- GPU configuration
- Quick presets for common scenarios

**generation_config.yaml** ⭐ NEW (LLM generation settings)
- Persona generation stage parameters (temperature, max_tokens for each stage)
- Tweet generation parameters
- Default NSFW and language settings
- Multi-GPU task queue timeouts

**utils/json_parser.py** (Shared JSON parsing utilities)
- `parse_llm_json_response()`: Unified LLM JSON parsing with fallback strategies
- `parse_calendar_json()`: Calendar-specific parsing with detailed error messages
- Handles markdown cleanup, quote normalization, and truncation fixes

**prompts/tweet_generation_prompt.py** (Fine-tuned prompts - DO NOT MODIFY)
- `_select_diverse_examples()`: Intelligent few-shot example selection based on:
  - Type diversity (avoid duplicate content types)
  - Mood diversity
  - Quality (scene_hint length 80-150 words)
  - Time segment diversity
- `get_persona_type_examples()`: Reference guide for persona styles (knowledge base, not dead code)
- `get_scene_hint_quality_guide()`: Image generation quality standards (knowledge base, not dead code)

**utils/calendar_manager.py** (Calendar generation - DO NOT MODIFY)
- Uses file locks for concurrent access safety
- Generates monthly content plans with topic distribution
- Preserves exact ComfyUI CalendarManager prompt logic

**core/tweet_generator.py** (Tweet generation core)
- `BatchTweetGenerator.generate_batch()`: Now accepts `context` parameter (refactored to eliminate wrapper)
- `_build_system_prompt()`: Contains LLM realism injection guidance (see docs/LLM_REALISM_INJECTION.md)
- Parsing expects exact format: `TWEET: [text]\nSCENE: [description]`
- If you change output format, update BOTH system prompt AND parser

**api/main.py** ⭐ NEW (FastAPI REST endpoints)
- `/generate/persona` - Generate persona from uploaded image
- `/generate/tweets` - Generate tweets for persona
- `/generate/images` - Generate images from tweet batch
- `/tasks/{task_id}` - Query async task status
- Celery integration for background processing

## Data Formats

### SillyTavern Character Card V2 (Persona Format)
```json
{
  "spec": "chara_card_v2",
  "spec_version": "2.0",
  "data": {
    "name": "Character Name",
    "description": "150-250 words",
    "personality": "250-300 words, Show Don't Tell",
    "system_prompt": "4-paragraph structure, 280 words",
    "extensions": {
      "twitter_persona": {
        "tweet_examples": [...],
        "appearance": {...}
      },
      "lora_config": {
        "model_path": "path/to/lora.safetensors",
        "strength": 0.8
      }
    }
  }
}
```

### Tweet Batch Output (with Image Generation Metadata)
```json
{
  "version": "1.0",
  "persona": {"name": "...", "lora": {...}},
  "tweets": [
    {
      "slot": 1,
      "tweet_text": "...",
      "image_generation": {
        "scene_hint": "...",
        "positive_prompt": "...",
        "lora_params": {"model_path": "...", "strength": 0.8},
        "generation_params": {"width": 768, "height": 1024, "steps": 28}
      }
    }
  ]
}
```

Output is compatible with ComfyUI's `TweetBatchLoader` node.

## Critical Constraints

### NSFW Content Generation Rules
Location: `core/tweet_generator.py:_build_system_prompt()`

These rules are CRITICAL to content quality:

1. **NO timestamps/dates**: Tweets are pre-generated, must not reference specific times
2. **Physical sensation over poetry**: Direct bodily feelings over metaphorical language
3. **Visual specificity**: Scene descriptions must be camera-ready with concrete details (angles, poses, clothing, lighting)
4. **Realism modifiers**: ALWAYS append 2-4 realism tokens to scene_hint (see LLM Realism Injection)

**DO NOT modify these rules** without understanding their purpose in maintaining quality and avoiding temporal inconsistencies.

### Prompt Engineering Principles

All prompts follow **"Show Don't Tell"** methodology:
- Describe behaviors, not labels
- Use specific scenes, not generic traits
- Demonstrate personality through actions

Example:
- ❌ "She is playful and flirty"
- ✅ "She bites her lower lip while typing, adds extra 'i's to words when excited, ends sentences with '~' when feeling mischievous"

### Configuration Management ⭐ NEW

**Two separate config files with different purposes:**

1. **`generation_config.yaml`** - LLM generation parameters
   - When to edit: Tuning LLM behavior (temperature, token limits)
   - Controls: Persona stages, tweet generation, example count
   - Hot-reload: Yes (no restart needed)

2. **`image_generation.yaml`** - Image model parameters
   - When to edit: Adjusting image quality/realism
   - Controls: Model selection, realism level, GPU settings, LoRA
   - Hot-reload: Yes (no restart needed)

**DO NOT** mix image model settings into `generation_config.yaml` or LLM settings into `image_generation.yaml`.

### Image Generation Approaches

**Two complementary systems for realism:**

1. **LLM Realism Injection** (Recommended, default)
   - Location: System prompt in `core/tweet_generator.py`
   - How: LLM adds realism tokens to scene_hint during generation
   - Pros: Context-aware, flexible, no post-processing
   - Cons: Requires prompt tuning for new models

2. **PromptEnhancer** (Alternative/Legacy)
   - Location: `core/prompt_enhancer.py`
   - How: Post-processes scene_hint with fixed token rules
   - Pros: Predictable, model-specific optimization
   - Cons: Less flexible, can add inappropriate tokens
   - Control: `image_generation.yaml` → `prompt_enhancement.enabled`

**Best Practice**: Use LLM injection for production. PromptEnhancer is useful for A/B testing or when LLM doesn't follow realism guidelines.

## Performance Tuning

### Concurrency Settings
- Most LLM APIs: Start with `--max-concurrent 20`
- If rate limited: Reduce to 5-10
- Local LLM deployments: Can increase to 50+

### API Compatibility
Any OpenAI-compatible API works (via `--api-base`):
- OpenAI, Claude via proxy, local models (Ollama, LM Studio)

### Multi-GPU Image Generation
- Single GPU: Sequential generation
- Multi-GPU: N×speedup (N = number of GPUs)
- Recommended: 4× A100/H100 GPUs achieve <10s/image (8 steps)

## Common Development Tasks

### Adding New LLM Provider
Modify `utils/llm_client.py` if custom headers/formats needed. Current implementation uses OpenAI async SDK which handles most compatible APIs.

### Modifying Tweet Generation Logic
**Location**: `core/tweet_generator.py`
- `_build_system_prompt()`: Base persona instructions + NSFW rules
- `_build_user_prompt()`: Calendar plan + context + examples

**Warning**: Prompts are fine-tuned. Changes may degrade quality or break parsing.

### Parsing LLM Responses
`_parse_response()` expects exact format:
```
TWEET: [tweet text]
SCENE: [scene description, may be multi-line]
```

If changing output format, update BOTH system prompt AND parser simultaneously.

## Directory Structure

```
auto-tweet-generator/
├── main.py                    # CLI entry point
├── generation_config.yaml     # ⭐ LLM generation parameters
├── config/
│   ├── image_generation.yaml  # ⭐ Image model parameters
│   ├── image_config.py        # ⭐ Config loader for image generation
│   ├── settings.py            # Environment variable handling
│   └── generation.py          # Config loader for LLM generation
├── api/                       # ⭐ FastAPI REST endpoints
│   ├── main.py                # API routes
│   └── models.py              # Pydantic request/response models
├── tasks/                     # ⭐ Celery background workers
│   ├── celery_app.py          # Celery configuration
│   └── generation_tasks.py    # Async generation tasks
├── core/                      # Core generation modules
│   ├── persona_generator.py   # 7-stage persona generation
│   ├── tweet_generator.py     # Tweet generation (with LLM realism injection)
│   ├── prompt_enhancer.py     # ⭐ Model-specific prompt enhancement
│   ├── image_generator.py     # Multi-GPU image generation
│   └── lora_support.py        # LoRA support (placeholder)
├── utils/                     # Utility modules
│   ├── llm_client.py          # Async LLM client with rate limiting
│   ├── calendar_manager.py    # Calendar generation (DO NOT MODIFY)
│   ├── json_parser.py         # Unified JSON parsing
│   ├── persona_utils.py       # Persona processing tools
│   └── file_lock.py           # Concurrent access safety
├── prompts/                   # Fine-tuned prompts (DO NOT MODIFY)
│   ├── core_generation_prompt.py
│   └── tweet_generation_prompt.py
├── tools/                     # External tool integrations
│   ├── datetime_tool.py       # Date/time with holiday detection
│   └── weather_tool.py        # OpenWeatherMap API
├── tests/                     # Test scripts
│   ├── test.sh                # Main test runner
│   └── test_zimage.py         # Z-Image environment test
├── scripts/                   # Utility scripts
│   ├── generation/            # Generation scripts
│   ├── maintenance/           # Maintenance tools
│   └── setup/                 # Setup scripts
├── docs/                      # Documentation
│   ├── README.md              # Documentation index
│   ├── guides/                # User guides (setup, workflows)
│   ├── features/              # ⭐ Feature docs (Content Pool, LLM Realism, PromptEnhancer)
│   ├── architecture/          # Architecture & design docs
│   ├── research/              # ⭐ Research reports & analysis
│   ├── reports/               # Development & test reports
│   └── writing/               # Writing guides (Chinese)
├── personas/                  # Persona JSON files
├── calendars/                 # Calendar JSON files
├── output_standalone/         # Tweet batch outputs
├── output_images/             # Generated images
├── image/                     # Test images
├── lora/                      # LoRA model symlinks
├── Z-Image/                   # Z-Image model (submodule)
├── legacy/                    # Historical ComfyUI code
├── .env                       # Environment variables (API keys, etc.)
├── start_api.sh               # ⭐ Start FastAPI + Celery
└── requirements.txt           # Python dependencies
```

## Relationship with ComfyUI

This system is extracted from ComfyUI custom nodes (`comfyui-twitterchat`). The original workflow used ComfyUI for orchestration, but core prompt engineering and generation logic is preserved here.

**Output Compatibility**: JSON format is designed to be compatible with ComfyUI's `TweetBatchLoader` node, allowing generated content to be imported back into ComfyUI workflows if needed.

**Migration Path**: To port changes back to ComfyUI nodes, modify the node's `generate()` method to call the same prompt building functions from `core/tweet_generator.py`.

## Code Quality Notes

**Recent Optimizations**:
- JSON parsing logic unified in `utils/json_parser.py` (eliminated 107 lines of duplication)
- Context flow refactored (removed 54 lines of redundant wrapper)
- Safe dictionary access in `image_generator.py` (prevents KeyError crashes)
- Knowledge base functions (`get_persona_type_examples`, `get_scene_hint_quality_guide`) are intentionally kept as reference documentation

**sys.path Manipulation**:
Multiple files use `sys.path.insert(0, ...)` for imports. While not ideal, this is necessary for the current structure. Consider using relative imports or PYTHONPATH configuration for future refactoring.

## Common Development Patterns

### Adding Realism Tokens to LLM Prompts

When modifying `core/tweet_generator.py:_build_system_prompt()`:
1. Group tokens by category (quality, authenticity, flaws, camera, lighting, atmosphere)
2. Provide contextual usage rules (e.g., "night scenes → low lighting")
3. Show examples with correct format
4. Test with multiple personas to ensure context-awareness

### Testing New Image Generation Parameters

1. Edit `config/image_generation.yaml` (no code restart needed)
2. Use presets for quick A/B testing: `balanced`, `authentic`, `high_quality`
3. Generate test images: `python main.py --generate-images --tweets-batch output_standalone/test_*.json`
4. Compare outputs in `output_images/`

### Debugging LLM JSON Parsing Failures

If `utils/json_parser.py` fails to parse LLM output:
1. Check logs for raw response text
2. Common issues: Extra markdown (```json), unescaped quotes, trailing commas
3. Add fallback strategy to `parse_llm_json_response()` if pattern is common
4. Update system prompt to clarify output format if LLM consistently fails

### Adjusting Concurrency for Rate Limits

If hitting API rate limits:
1. Edit `.env`: `MAX_CONCURRENT=5` (reduce from default 20)
2. Or use command line: `--max-concurrent 5`
3. Monitor logs for 429 errors
4. For local models, can increase to 50+

### Modifying Persona Generation Pipeline

**WARNING**: Stages 1-7 have dependencies. If modifying:
1. Read `docs/architecture/persona_generation_plan.md` first
2. Stage order must be preserved (e.g., Stage 3 examples need Stage 2 strategy)
3. Test with `python main.py --generate-persona --image test.png`
4. Verify JSON output contains all required fields for downstream tweet generation

### Working with LoRA Models

LoRA configuration is in persona JSON under `extensions.lora_config`:
```json
{
  "extensions": {
    "lora_config": {
      "model_path": "lora/character_name.safetensors",
      "strength": 0.8
    }
  }
}
```

To add LoRA to existing personas:
- Use script: `python scripts/maintenance/update_lora_in_tweets.py`
- Or edit manually following SillyTavern V2 schema
