# Documentation Index

Complete documentation for the auto-tweet-generator project.

## Quick Links

- **[Main README](../README.md)** - Project overview and setup
- **[CLAUDE.md](../CLAUDE.md)** - AI assistant guidance and project structure

## 📚 Documentation Structure

### User Guides (`guides/`)
Step-by-step guides for common workflows:

- **[Persona Generation Guide](guides/PERSONA_GENERATION_GUIDE.md)** - Creating AI personas from images
- **[Batch Generation Guide](guides/BATCH_GENERATION_GUIDE.md)** - High-concurrency batch tweet generation
- **[Performance Guide](guides/PERFORMANCE_GUIDE.md)** - Performance tuning and optimization
- **[Concurrency Guide](guides/CONCURRENCY_GUIDE.md)** - Concurrency configuration and best practices
- **[Z-Image Setup](guides/ZIMAGE_SETUP.md)** - Z-Image model setup instructions

### Features (`features/`)
Feature-specific documentation:

#### Content Generation
- **[Content Pool System](features/CONTENT_POOL_SYSTEM.md)** ⭐ **DEFAULT** - Generate tweets by content type (no calendar needed)
- **[Content Pool Default Mode](features/CONTENT_POOL_DEFAULT.md)** - Quick start guide for content pool mode
- **[Advanced Generation](features/ADVANCED_GENERATION_GUIDE.md)** - Advanced generation strategies
- **[Advanced Generation Implementation](features/ADVANCED_GENERATION_IMPLEMENTATION_SUMMARY.md)** - Implementation details

#### Image Generation
- **[LLM Realism Injection](features/LLM_REALISM_INJECTION.md)** ⭐ **RECOMMENDED** - Real-world photography effects via LLM
- **[PromptEnhancer Guide](features/PROMPT_ENHANCER_GUIDE.md)** - Model-specific prompt enhancement system
- **[PromptEnhancer Summary](features/PROMPT_ENHANCER_SUMMARY.md)** - Quick reference

#### Market Optimization
- **[US Market Optimization](features/US_MARKET_OPTIMIZATION.md)** - Mirror selfies and engagement strategies

### Architecture (`architecture/`)
System design and technical architecture:

- **[Persona Generation Plan](architecture/persona_generation_plan.md)** - 7-stage persona generation pipeline
- **[Config System](architecture/CONFIG_SYSTEM.md)** - Configuration management guide
- **[Config System Summary](architecture/CONFIG_SYSTEM_SUMMARY.md)** - Configuration architecture overview
- **[Config Migration Examples](architecture/CONFIG_MIGRATION_EXAMPLES.py)** - Code examples for config usage
- **[Concurrency Optimizations](architecture/CONCURRENCY_OPTIMIZATIONS.md)** - Async concurrency implementation
- **[Concurrency Safety Review](architecture/CONCURRENCY_SAFETY_REVIEW.md)** - Thread safety analysis

### Research (`research/`)
Research reports and analysis:

- **[Image Generation Research Report](research/IMAGE_GENERATION_RESEARCH_REPORT.md)** - Architecture design and implementation
- **[Z-Image Advanced Workflow Analysis](research/ZIMAGE_ADVANCED_WORKFLOW_ANALYSIS.md)** - Z-Image workflow deep dive
- **[跨文化视觉美学报告](research/跨文化视觉美学报告.md)** - Cross-cultural visual aesthetics (Chinese)

### Reports (`reports/`)
Development and test reports:

- **[Development Summary](reports/DEVELOPMENT_SUMMARY.md)** - Project summary and capabilities
- **[Optimization Test Report](reports/OPTIMIZATION_TEST_REPORT.md)** - Mirror selfie & realism optimization results
- **[Verification Report](reports/VERIFICATION_REPORT.md)** - Standalone vs ComfyUI verification
- **[CLAUDE.md Improvements](reports/CLAUDE_MD_IMPROVEMENTS.md)** - Documentation improvements log

### Writing Guides (`writing/`)
Chinese content creation guides:

- **[人设撰写指南](writing/人设撰写指南.md)** - Persona writing guide
- **[角色卡撰写指南](writing/角色卡撰写指南.md)** - Character card writing guide

## 🚀 Quick Start

### New Users
1. Read [Main README](../README.md) for project overview
2. Follow [Z-Image Setup](guides/ZIMAGE_SETUP.md) for environment setup
3. Try [Content Pool Default Mode](features/CONTENT_POOL_DEFAULT.md) for your first generation

### Development
1. Read [CLAUDE.md](../CLAUDE.md) for project structure and conventions
2. Check [Architecture docs](architecture/) for system design
3. Review [Config System](architecture/CONFIG_SYSTEM.md) for configuration management

## 🎯 Key Concepts

### Persona Generation (7-Stage Pipeline)
1. **Core Persona**: Vision model analyzes image → base persona
2. **Tweet Strategy**: Content type distribution planning
3. **Example Tweets**: 8 high-quality reference tweets
4. **Social Network**: Friend relationships and interactions
5. **Realism System**: Typos, flaws, authentic patterns
6. **Visual Archive**: Outfit/pose/lighting preferences
7. **Knowledge Base**: Character book entries

See [Persona Generation Plan](architecture/persona_generation_plan.md) for details.

### Tweet Generation Modes

#### Content Pool Mode (⭐ Default)
- **No calendar needed**
- Generates tweets by content type distribution
- Automatic diversity tracking
- Best for: Batch generation, quick testing

See [Content Pool System](features/CONTENT_POOL_SYSTEM.md)

#### Calendar Mode (Traditional)
- Requires calendar generation
- Generates tweets by date
- Long-term content planning
- Best for: Scheduled content campaigns

See [Batch Generation Guide](guides/BATCH_GENERATION_GUIDE.md)

### Image Generation Approaches

#### LLM Realism Injection (⭐ Recommended)
Real-world photography effects injected through LLM guidance:
- Context-aware realism tokens
- Scene-appropriate flaws (blur, grain, lighting issues)
- Intelligent selection based on scenario

See [LLM Realism Injection](features/LLM_REALISM_INJECTION.md)

#### PromptEnhancer (Alternative)
Model-specific prompt enhancement:
- Z-Image: Realism tokens
- SDXL: Photography quality tokens
- 3-level realism (LOW/MEDIUM/HIGH)
- Rule-based post-processing

See [PromptEnhancer Guide](features/PROMPT_ENHANCER_GUIDE.md)

## 📦 Project Structure

```
auto-tweet-generator/
├── api/                    # FastAPI REST endpoints
├── config/                 # Configuration management
│   ├── image_generation.yaml
│   ├── archetypes.yaml
│   └── content_types.yaml
├── core/                   # Core generation modules
│   ├── persona_generator.py
│   ├── tweet_generator.py
│   ├── image_generator.py
│   ├── prompt_enhancer.py
│   └── content_planner.py
├── docs/                   # Documentation (you are here)
│   ├── guides/            # User guides
│   ├── features/          # Feature documentation
│   ├── architecture/      # System design
│   ├── research/          # Research reports
│   ├── reports/           # Development reports
│   └── writing/           # Writing guides (Chinese)
├── prompts/                # Fine-tuned prompts (DO NOT MODIFY)
├── scripts/                # Utility scripts
├── utils/                  # Shared utilities
├── generation_config.yaml  # LLM generation parameters
└── README.md              # Main project README
```

## 🔍 Finding Documentation

### By Task
- **Setup environment** → [Z-Image Setup](guides/ZIMAGE_SETUP.md)
- **Generate personas** → [Persona Generation Guide](guides/PERSONA_GENERATION_GUIDE.md)
- **Generate tweets** → [Content Pool Default Mode](features/CONTENT_POOL_DEFAULT.md)
- **Batch generation** → [Batch Generation Guide](guides/BATCH_GENERATION_GUIDE.md)
- **Tune performance** → [Performance Guide](guides/PERFORMANCE_GUIDE.md)
- **Improve image realism** → [LLM Realism Injection](features/LLM_REALISM_INJECTION.md)

### By Component
- **Persona pipeline** → [Persona Generation Plan](architecture/persona_generation_plan.md)
- **Configuration** → [Config System](architecture/CONFIG_SYSTEM.md)
- **Concurrency** → [Concurrency Guide](guides/CONCURRENCY_GUIDE.md)
- **Image generation** → [Image Generation Research](research/IMAGE_GENERATION_RESEARCH_REPORT.md)

### By Topic
- **Content strategy** → [Content Pool System](features/CONTENT_POOL_SYSTEM.md)
- **Market optimization** → [US Market Optimization](features/US_MARKET_OPTIMIZATION.md)
- **Writing personas** → [人设撰写指南](writing/人设撰写指南.md)

## 📝 Contributing

When adding documentation:
1. Place user guides in `guides/`
2. Place feature docs in `features/`
3. Place architecture docs in `architecture/`
4. Place research in `research/`
5. Update this index with proper category
6. Use clear, descriptive titles
7. Add ⭐ marker for recommended/default approaches

## 💡 Documentation Standards

- **User guides**: Step-by-step instructions, examples, troubleshooting
- **Features**: Feature overview, usage, configuration, examples
- **Architecture**: Design decisions, implementation details, diagrams
- **Research**: Analysis, experiments, findings, recommendations
- **Reports**: Test results, summaries, verification logs

## 🆘 Support

- **GitHub Issues**: Report bugs or request features
- **CLAUDE.md**: Guidance for AI assistants working with this codebase
- **Main README**: Quick start and common commands
