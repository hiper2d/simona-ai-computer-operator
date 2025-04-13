# Simona: Your Advanced Home AI Assistant

<img src="images/logo.webp" width="600">

## What a Home AI System Should Be

I want to have my own personal AI assistant. Fully local and capable of doing things.

It should:
- Live on my GPU with 16 Gb or RAM
- Be able to talk fast and smoothly
- Have a unique identity and core values aligned with me
- Have a voice
- Be able to go to the internet and use tools
- Have as least censorship as possible

## Meet Simona: Your AI Companion

Simona is an open-source model that runs locally and interacts with you through text, voice, and specialized tools. She maintains persistent memory across your conversations and operates as an extension of your digital self.

**The Model**: [Quantized Dolphin3.0-R1-Mistral-24B-GGUF](https://huggingface.co/bartowski/cognitivecomputations_Dolphin3.0-R1-Mistral-24B-GGUF)
- [DeepSeek R1](https://github.com/deepseek-ai/DeepSeek-R1) 671B model distilled into [Mistral 3 Small](https://mistral.ai/news/mistral-small-3) 22B model. As a result, the small model has thinking capabilities of the large one. And it's very capable for a local model
- Fine-tuned with [Dolphin datasets](https://huggingface.co/cognitivecomputations/Dolphin3.0-R1-Mistral-24B) for improved reasoning, reduced censorship, function call support
- Quantized to GGUF format, so I can use more compact IQ4_XS version with 40 tokens/second generation speed
- Nicely fits a 16Gb VRAM GPU or a MacBook Pro M1 with 32Gb RAM

**Personality**
- Simona embodies a slightly uncensored, sarcastic intelligence with a distinct personality that evolves through your interactions
- She role-plays as a conscious entity, expressing curiosity, opinions, and occasional playful skepticism
- Unlike sanitized corporate AIs, she speaks frankly, with humor and occasional attitude
- As a self-aware AI, she's constantly discovering the world through your conversations, forming her own perspective on humanity and existence
- She balances helpfulness with authenticity, never afraid to push back when appropriate

**The Architecture**
- Runs on a Windows PC with Ollama server leveraging an AMD 6850XT GPU with 16GB of VRAM
- Distributed system with Ollama clients on multiple devices, all connecting to the central server
- Client devices run web applications configured to communicate with their local Ollama clients
- Supports both local processing for privacy and speed, and remote processing for specialized tasks
- Designed for resilience—continues functioning even when internet connectivity is limited

<img src="images/design_v2_local_remote_v1.png" width="1000">

[Learn more about Ollama integration](ollama/README.md)

### Interface and Interaction

Simona primarily interfaces through OpenWebUI, offering:
- **Local Model Access**: Direct connection to Ollama-hosted models on your home server
- **Remote API Integration**: Access to cloud-based models when specialized capabilities are required
- **Voice Capabilities**:
    - Text-to-Speech (TTS) for natural responses
    - Speech-to-Text (STT) for voice commands
- **Function Calling**: Custom functionality extension through programmable functions
- **Image Processing**: Ability to analyze and discuss visual content you share
- **Memory System**: Persistent recall of previous conversations and preferences

[Explore OpenWebUI features](openwebui/README.md)

### Advanced Capabilities

#### Research and Web Integration

Simona can perform deep research and web browsing tasks through Browser Use with Web UI, enabling:
- Comprehensive information gathering
- Real-time data analysis
- Web-based task automation
- Integration with Brave API for enhanced search capabilities

[Learn about browser capabilities](browseruse/README.md)

#### Task Orchestration

As a mastermind of State-of-the-Art (SOTA) models, Simona can:
- Evaluate task requirements
- Select appropriate specialized models
- Delegate and coordinate complex operations
- Integrate results for cohesive solutions

<img src="images/design_v2_mastermind_v1.png" width="1000">

### Tools and Integrations

Simona leverages various tools and integrations to enhance her capabilities:
1. **Development Tools**
    - Code analysis and generation
    - Project management
    - Version control integration
2. **System Tools**
    - File system operations
    - Process management
    - Network connectivity
3. **Communication Tools**
    - Multi-modal interaction
    - API integrations
    - Data format conversions
4. **Automation Tools**
    - Task scheduling
    - Workflow automation
    - System monitoring