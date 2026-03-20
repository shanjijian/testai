# TestAI 👋

![GitHub stars](https://img.shields.io/github/stars/shanjijian/testai?style=social)
![GitHub forks](https://img.shields.io/github/forks/shanjijian/testai?style=social)
![GitHub last commit](https://img.shields.io/github/last-commit/shanjijian/testai?color=blue)
![GitHub top language](https://img.shields.io/github/languages/top/shanjijian/testai)
![GitHub repo size](https://img.shields.io/github/repo-size/shanjijian/testai)
![GitHub license](https://img.shields.io/github/license/shanjijian/testai)


**TestAI is a powerful, extensible, and user-friendly AI agent framework designed for complex task automation.** It leverages the **DeepAgents** ecosystem to provide **multi-agent coordination**, **secure code execution**, and **real-time streaming interactions**, making it an **advanced AI deployment solution**.

[English](README.md) | [简体中文](README_zh.md)

---

## 🚀 Key Features

- 🌊 **Real-time Streaming**: "Typewriter" effect for ultra-smooth AI interactions.
- 🔬 **Deep Research**: Multi-agent coordination for large-scale information gathering and synthesis.
- 💻 **Secure Sandbox**: Isolated Python and Shell execution environment via OpenSandbox.
- 🗄️ **Production Persistence**: Full chat history and file storage with PostgreSQL and Tencent COS.
- 🎨 **Modern Web UI**: Premium conversational interface built with Chainlit.
- 📊 **Full Observability**: Integrated Langfuse tracing and structured logging.

---

## 📦 Quick Start

### 1. Installation
```bash
git clone https://github.com/shanjijian/testai.git
cd testai
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp .env.example .env
cp configs/config.yaml.example configs/config.yaml
# Edit .env with your API keys
```

### 3. Launch Infrastructure
```bash
docker-compose -f docker/docker-compose.yaml up -d
```

### 4. Run the UI
```bash
chainlit run src/ui/chainlit_app.py
```

### 5. Connect to Open WebUI (OpenAI API)
TestAI provides an OpenAI-compatible API for seamless integration:
```bash
export PYTHONPATH=$PYTHONPATH:.
python src/ui/api_server.py
```
In Open WebUI settings:
- **API Base URL**: `http://localhost:8000/v1`
- **API Key**: `testai`
- **Model**: `testai-agent`

---

## 🤝 Contributing & Support

We welcome contributions! Please check our [Contributing Guide](./CONTRIBUTING.md).
For support, feel free to open an issue or check the documentation.

---

## 📄 License

TestAI is licensed under the [MIT License](./LICENSE).
