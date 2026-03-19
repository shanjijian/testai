# TestAI - 基于 DeepAgents 的 Agent 框架开发示例

> **TestAI** 是一个展示如何使用 [**DeepAgents**](https://github.com/langchain-ai/deepagents) 框架构建多代理协作、带代码执行沙箱且具备异步持久化能力的智能代理平台的**参考示例**。

本项目不仅仅是一个可以直接运行的代码库，更是一份使用 DeepAgents 架构最佳实践的工程指南。它演示了如何高效组织 Agent 核心逻辑、基础设施层以及工具链。

---

## 🚀 核心特性

- **多代理协作** (Multi-Agent Collaboration)：通过主代理协调多个子代理（研究专家、代码执行专家）完成复杂任务。
- **安全沙箱执行** (OpenSandbox)：在隔离的沙箱环境中执行 Python 代码和 Shell 命令，确保宿主机安全。
- **持久化记忆池** (Persistence Store)：采用 PostgreSQL 16 处理海量会话历史，支持多用户/多线程隔离。
- **多端存储集成**：深度集成腾讯云 COS，支持生成加密后的文件报告下载链接。
- **结构化配置管理**：采用嵌套的 Pydantic 模型，支持 YAML 模板与环境变量的动态映射。
- **全栈监控**：集成 Langfuse 追踪（Trace）和 Loguru 结构化日志，方便调试与审计。

---

## 🛠️ 项目结构

```text
testai/
├── src/
│   ├── core/           # 核心逻辑 (Agent, Prompt, Config, Logger)
│   ├── infrastructure/ # 基础设施 (Database, Sandbox)
│   ├── agents/         # 子代理定义 (Sub-Agents)
│   ├── tools/          # 自定义工具集 (Search, Cloud, Sandbox)
│   └── utils/          # 通用工具函数 (Logging Utilities)
├── configs/            # 配置文件模板
├── docker/             # 容器化部署脚本 (PostgreSQL, OpenSandbox)
├── skills/             # 技能/工具定义目录
├── main.py             # 项目入口
└── .env                # 环境变量 (本地/敏感配置)
```

---

## 📦 快速开始

### 1. 环境准备
- Python 3.10+
- Docker & Docker Compose
- Conda (推荐)

### 2. 安装依赖
```bash
git clone https://github.com/your-username/testai.git
cd testai
pip install -r requirements.txt
```

### 3. 配置环境
复制配置模板并填写您的 API 密钥：
```bash
cp .env.example .env
cp configs/config.yaml.example configs/config.yaml
```

### 4. 启动基础设施
```bash
docker-compose -f docker/docker-compose.yaml up -d
```

### 5. 运行代理
```bash
python main.py --query "帮我分析京东云目前最受关注的安全产品并写一份报告。"
```

### 6. 可选：配置 Langfuse 观测 (Monitoring)
本项目集成 Langfuse 用于追踪 Agent 思考过程。
- **云端版**: 在 [langfuse.com](https://cloud.langfuse.com) 注册获取 Key，设置 `.env` 中的 `LANGFUSE_BASE_URL=https://cloud.langfuse.com`。
- **本地版**: 
  ```bash
  docker-compose -f docker/langfuse/docker-compose.yml up -d
  ```
  访问 `http://localhost:3000` 获取 Key，并将 `LANGFUSE_BASE_URL` 设置为本地地址。

### 7. 启动 Web 界面 (Chainlit)
本项目支持通过 Chainlit 提供的交互式 Web 界面进行对话。
```bash
chainlit run src/ui/chainlit_app.py
```
访问 `http://localhost:8000` 即可开始对话，您可以直观地看到子代理的工作步骤。

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 以了解如何开始。

## 📄 开源协议

本项目采用 [MIT License](./LICENSE) 开源协议。
