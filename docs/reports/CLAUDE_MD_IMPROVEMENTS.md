# CLAUDE.md Improvements Summary

This document summarizes the improvements made to CLAUDE.md based on the `/init` command analysis.

## What Was Added

### 1. **Recent Major Features Section** (New)
Added prominent callout of recent architectural improvements:
- LLM Realism Injection system
- PromptEnhancer architecture
- FastAPI REST API with Celery
- Dual configuration system (generation_config.yaml + image_generation.yaml)

### 2. **Enhanced Testing Commands** (Expanded)
**Before**: Only mentioned `cd tests && bash test.sh`

**After**: Added specific test commands:
- `python tests/test_zimage.py` - Test Z-Image environment
- `python test_llm_realism.py` - Test LLM realism injection
- `python test_prompt_enhancer.py` - Test prompt enhancer
- `python test_tweet_length.py` - Test tweet length validation

### 3. **API Server Documentation** (New)
Added complete FastAPI + Celery setup instructions:
- Redis dependency setup (macOS/Linux/Docker)
- `bash start_api.sh` startup command
- API endpoint URLs (Swagger docs, health check, Celery Flower)

This was completely missing from the original CLAUDE.md.

### 4. **Architecture Section Enhancements** (Major Update)

#### Added Pattern #3: LLM Realism Injection System
- Explains how realism tokens are injected via LLM guidance
- Scene-aware selection rules
- Critical note about superiority over post-processing

#### Added Pattern #4: PromptEnhancer System
- Decoupled architecture explanation
- Model-specific implementations (Z-Image vs SDXL)
- 3-level realism system
- How to disable via config

#### Added Pattern #5: Dual Configuration System
- Separation of concerns: LLM params vs Image params
- When to edit each config file
- Hot-reload capability
- Warning about not mixing configs

### 5. **Key Files Documentation** (Expanded)

Added critical new files:
- `core/prompt_enhancer.py` - Model-specific prompt enhancement
- `config/image_config.py` - Configuration management
- `config/image_generation.yaml` - Image generation settings
- `generation_config.yaml` - LLM generation settings
- `api/main.py` - FastAPI REST endpoints

Enhanced existing file descriptions:
- `core/tweet_generator.py` - Now mentions LLM realism injection guidance

### 6. **Configuration Management Section** (New)

Added detailed explanation of:
- Two separate config files with different purposes
- When to edit each file
- What each file controls
- Hot-reload capability
- Warning about not mixing concerns

### 7. **Image Generation Approaches Section** (New)

Explains two complementary systems:
1. **LLM Realism Injection** (Recommended)
   - Location, how it works, pros/cons
2. **PromptEnhancer** (Alternative/Legacy)
   - Location, how it works, pros/cons
   - How to control via config

Best practice guidance included.

### 8. **Enhanced NSFW Rules** (Updated)

Added 4th critical rule:
- **Realism modifiers**: ALWAYS append 2-4 realism tokens to scene_hint

### 9. **Directory Structure** (Major Update)

**Before**: Basic structure with ~15 entries

**After**: Comprehensive structure with 40+ entries including:
- `generation_config.yaml` ⭐
- `config/` directory with all files
- `api/` directory (FastAPI)
- `tasks/` directory (Celery)
- `core/prompt_enhancer.py` ⭐
- Detailed `docs/` structure with new guides
- `start_api.sh` ⭐

All new/important items marked with ⭐ symbol.

### 10. **Common Development Patterns Section** (New)

Added 6 practical subsections:

1. **Adding Realism Tokens to LLM Prompts**
   - Step-by-step guide
   - Testing recommendations

2. **Testing New Image Generation Parameters**
   - How to use YAML presets for A/B testing
   - No-restart workflow

3. **Debugging LLM JSON Parsing Failures**
   - Common issues checklist
   - Where to add fallback strategies

4. **Adjusting Concurrency for Rate Limits**
   - .env vs command-line configuration
   - Monitoring tips
   - Local model scaling

5. **Modifying Persona Generation Pipeline**
   - Critical warnings about dependencies
   - Required reading before changes
   - Testing workflow

6. **Working with LoRA Models**
   - JSON schema example
   - Maintenance script reference

## What Was NOT Changed

Following the instructions, these were intentionally NOT added:
- Generic development practices
- Obvious instructions like "Write unit tests"
- Comprehensive file listings (kept high-level only)
- Made-up "Tips for Development" sections

## Summary Statistics

- **Lines added**: ~120 lines of new content
- **Sections added**: 5 major new sections
- **Sections enhanced**: 4 existing sections significantly improved
- **New files documented**: 8 critical new files
- **New commands documented**: 5 test commands + API server startup

## Key Improvements for Future Claude Instances

1. **Immediate awareness of recent features** (LLM Realism Injection, PromptEnhancer)
2. **Clear testing workflow** (all test commands in one place)
3. **Production deployment guide** (API server setup)
4. **Configuration best practices** (dual config system explained)
5. **Practical development patterns** (common tasks with step-by-step guides)
6. **Architecture understanding** (7 design patterns vs original 4)

This ensures future Claude Code sessions can be productive immediately without needing to explore the codebase to understand recent architectural decisions.
