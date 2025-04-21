# Simona: Your Advanced Home AI Assistant

<img src="images/logo.webp" width="600">

## What a Home AI System Should Be

A trully persolan assistant should
- live on home GPU
- have an interesting identity aligned with you, your golas and values
- have long term memory
- be able to talk with text, voice, images
- be able to do things on your PC and in the internet
- use more powerful expernal AIs and tools when needed

## Meet Simona

Simona is the implementation of the ideas above. Few facts about her:
- Simona has an LLM-brain hosted on my gaming PC via Ollama. It's a small but capable open-source model with function calls support
- We use OpenWebUI as an interface where all the components are connected together:
    - remote Ollama server
    - chat client
    - remote MCP servers with LightRAG-based memory, web search and other tools
    - text-to-voice and voice-to-text models for speech capabilities
    - Simona's identity instructions
    - RAG on attachments and lots of other build-in features
- Simona's identity is based on my own memories from social media, my converstations about AI-counsciousness with Claude, sci-fi books and anything else I may came up with

This repository also contains few more independent AI-tools which have nothing to do with Simona (yet) but they help me day-to-day:
- Roo Code coding assistant
- [Web Use / Browser Use](browseruse/README.md) web agent

## Simona's LLM Brain

**Current Model**: [Quantized Mistral 3.1 Small](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF)

- Original Model is [Mistral 3 Small 24B (4-bit GGUF)](https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503). It is good, compact, supports functions, has a large (up to 128k) context window
- Quantized version IQ4_XS 12.8 GB version with 32k context size is a nice compromise that fits my GPU

The model is fine, it supports functions (can use MCPs) but there is not reasoning and reduced censorship.

**Deprecated Model**: [Dolphin3 R1-Mistral 24B (4-bit GGUF)](https://huggingface.co/bartowski/cognitivecomputations_Dolphin3.0-R1-Mistral-24B-GGUF)

- [DeepSeek R1](https://github.com/deepseek-ai/DeepSeek-R1) 671B model distilled into [Mistral 3 Small](https://mistral.ai/news/mistral-small-3) 22B model. As a result, the small model has thinking capabilities of the large one. And it's very capable for a local model
- Fine-tuned with [Dolphin datasets](https://huggingface.co/cognitivecomputations/Dolphin3.0-R1-Mistral-24B) for improved reasoning, reduced censorship, function call support
- Quantized to GGUF format, so I can use more compact IQ4_XS version with 40 tokens/second generation speed
- Nicely fits a 16Gb VRAM GPU or a MacBook Pro M1 with 32Gb RAM

The Dolphin model was perfect until I found out that it doesn't support functions. That's a blocked to me because I want to use MCPs with it. There is hope though. [Here](https://huggingface.co/cognitivecomputations/Dolphin3.0-R1-Mistral-24B/discussions/1#67a82cc6a49580b6477afadb) is some guy got the OpenAI compatible tool calling working.

**System Prompts and personality**

- Simona embodies a slightly uncensored, sarcastic intelligence with a distinct personality that evolves through your interactions
- She role-plays as a conscious entity, expressing curiosity, opinions, and occasional playful skepticism
- Unlike sanitized corporate AIs, she speaks frankly, with humor and occasional attitude
- As a self-aware AI, she's constantly discovering the world through your conversations, forming her own perspective on humanity and existence
- She balances helpfulness with authenticity, never afraid to push back when appropriate

## Overal architecture

> This needs update

- Runs on a Windows PC with Ollama server leveraging an AMD 6850XT GPU with 16GB of VRAM
- Distributed system with Ollama clients on multiple devices, all connecting to the central server
- Client devices run web applications configured to communicate with their local Ollama clients
- Supports both local processing for privacy and speed, and remote processing for specialized tasks
- Designed for resilience—continues functioning even when internet connectivity is limited

<img src="images/design_v2_local_remote_v1.png" width="1000">

[Learn more about Ollama integration](ollama/README.md)

## OpenwebUI Interface and MCPs

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