# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a standalone high-concurrency NSFW tweet generation system that **completely decouples from ComfyUI** while **preserving all fine-tuned prompts and logic** from the original ComfyUI workflow. It directly calls LLM APIs using async Python to generate AI persona content.

**Core Design**: The system retains ComfyUI-based prompt engineering and generation logic while replacing the ComfyUI execution layer with direct async LLM API calls, achieving 5-10x performance improvement through native concurrency.

**Critical**: All prompts, calendar generation logic, and content strategies are **copied verbatim** from the original ComfyUI nodes. Do NOT modify these fine-tuned prompts without understanding their purpose.

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
# Run test suite
cd tests && bash test.sh

# Note: Tests expect files at ../personas/*.json and ../calendars/*.json
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

**2. Generate tweets:**
```bash
python main.py \
  --persona personas/my_character.json \
  --tweets 10 \
  --generate-calendar \
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

**3. Context Flow**
```
main.gather_context()
  → BatchTweetGenerator.generate_batch(context=xxx)
    → StandaloneTweetGenerator.generate_single_tweet(context=xxx)
```

Context includes date/weather and is injected into tweet generation prompts.

**4. Multi-GPU Image Generation**
Location: `core/image_generator.py`

Uses `torch.multiprocessing` with process pools:
- Single GPU: Sequential generation
- Multi-GPU: Task queue distributes to different GPUs, result queue collects outputs
- LoRA support via Diffusers mode (auto-load/unload to avoid contamination)

### Key Files and Their Roles

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
- Parsing expects exact format: `TWEET: [text]\nSCENE: [description]`
- If you change output format, update BOTH system prompt AND parser

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

**DO NOT modify these rules** without understanding their purpose in maintaining quality and avoiding temporal inconsistencies.

### Prompt Engineering Principles

All prompts follow **"Show Don't Tell"** methodology:
- Describe behaviors, not labels
- Use specific scenes, not generic traits
- Demonstrate personality through actions

Example:
- ❌ "She is playful and flirty"
- ✅ "She bites her lower lip while typing, adds extra 'i's to words when excited, ends sentences with '~' when feeling mischievous"

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
├── main.py                    # Entry point with coordinators
├── core/                      # Core generation modules
│   ├── persona_generator.py   # 7-stage persona generation
│   ├── tweet_generator.py     # Tweet generation
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
├── docs/                      # Documentation
├── personas/                  # Persona JSON files
├── calendars/                 # Calendar JSON files
├── output_standalone/         # Tweet batch outputs
├── output_images/             # Generated images
├── image/                     # Test images
├── lora/                      # LoRA model symlinks
├── Z-Image/                   # Z-Image model (submodule)
└── legacy/                    # Historical ComfyUI code
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
