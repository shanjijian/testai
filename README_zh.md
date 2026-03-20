# TestAI 👋

![GitHub stars](https://img.shields.io/github/stars/shanjijian/testai?style=social)
![GitHub forks](https://img.shields.io/github/forks/shanjijian/testai?style=social)
![GitHub last commit](https://img.shields.io/github/last-commit/shanjijian/testai?color=blue)
![GitHub top language](https://img.shields.io/github/languages/top/shanjijian/testai)
![GitHub repo size](https://img.shields.io/github/repo-size/shanjijian/testai)
![GitHub license](https://img.shields.io/github/license/shanjijian/testai)


**TestAI 是一个高性能、可扩展且用户友好的 AI Agent 框架，专为处理复杂任务自动化而设计。** 它基于 **DeepAgents** 生态，支持**多智能体协作**、**安全代码执行**以及**全流式实时交互**，是一个功能强大的 **AI 部署解决方案**。

[English](README.md) | [简体中文](README_zh.md)

---

## 🚀 核心特性

- 🌊 **全流式交互**：极致流畅的“打字机”实时输出体验。
- 🔬 **深度研究**：协同多个子代理进行互联网级信息调研与知识整合。
- 💻 **安全代码沙箱**：通过 OpenSandbox 在隔离环境中运行 Python 与 Shell。
- 🗄️ **生产级持久化**：集成 PostgreSQL 处理海量会话，腾讯云 COS 负责文件存储。
- 🎨 **现代 Web UI**：基于 Chainlit 构建的高级对话界面，支持思考步骤可视化。
- 📊 **全栈观测性**：深度集成 Langfuse 追踪与结构化日志审计。

---

## 📦 快速开始

### 1. 安装项目
```bash
git clone https://github.com/shanjijian/testai.git
cd testai
pip install -r requirements.txt
```

### 2. 配置环境
```bash
cp .env.example .env
cp configs/config.yaml.example configs/config.yaml
# 在 .env 中填写您的 API 密钥
```

### 3. 启动基础设施
```bash
docker-compose -f docker/docker-compose.yaml up -d
```

### 4. 启动 Web 界面 (二选一)

#### 选项 A: 使用原生 Chainlit UI (简单快速)
```bash
chainlit run src/ui/chainlit_app.py
```

#### 选项 B: 使用 Open WebUI (功能丰富)
1. **启动 Open WebUI 容器**:
   ```bash
   docker-compose -f docker/open-webui/docker-compose.yaml up -d
   ```
2. **启动 TestAI API 服务**:
   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   python src/api/main.py
   ```
3. **访问界面**: 打开 [http://localhost:3000](http://localhost:3000)
   - **API Base URL**: `http://host.docker.internal:8000/v1` (macOS/Windows) 或 `http://<宿主机IP>:8000/v1` (Linux)
   - **API Key**: `testai`
   - **Model**: `testai-agent`

---

## 🤝 贡献与支持

欢迎任何形式的贡献！请参考 [贡献指南](./CONTRIBUTING.md)。
如有疑问，欢迎提交 Issue 或阅读官方文档。

---

## 📄 开源协议

TestAI 采用 [MIT License](./LICENSE) 开源协议。
