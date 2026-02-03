# Vibe Nexus 框架

Vibe Nexus 是一个基于辩论式AI协作的项目生成框架。它利用多个AI提供者之间的智能辩论过程，自动生成高质量的项目结构和代码。

## 核心特性

- **辩论式AI协作**: 利用两个不同的AI提供者（如Google Gemini和Zhipu GLM）进行观点辩论，生成更完善的解决方案
- **模块化架构**: 遵循模块化驱动原则，所有提供者都继承自统一的基础类
- **环境变量管理**: 通过.env文件安全地管理API密钥等敏感信息
- **鲁棒性设计**: 具备错误处理和降级机制，确保系统稳定性
- **目录隔离**: 生成的项目代码完全隔离在output/目录下，不污染根目录
- **PnC准则**: 每个任务都包含物理路径(target_path)和验证步骤(verification)

## 宪法原则

Vibe Nexus 严格遵循其核心宪法，确保代码质量和架构一致性：

### 框架开发约束 (Meta Rules)
- **模块化驱动**: 所有 Provider (Gemini/GLM) 必须继承自 Base 类，严禁硬编码
- **环境变量感知**: 严禁在代码中硬编码 API Key，必须通过 `.env` 读取
- **鲁棒性**: 必须处理网络超时和 JSON 解析失败的情况，提供降级输出

### 架构生成约束 (Architecture Rules)
- **目录隔离**: 业务代码必须存在于 `output/项目名/src` 目录下，严禁污染根目录
- **协议先行**: 模块间通信必须定义明确的数据模型 (Pydantic/Interface)
- **PnC 准则**: 所有任务 (Tasks) 必须包含物理路径 (`target_path`) 和可执行的验证步骤 (`verification`)

### 辩论准则 (Debate Rules)
- **冲突挖掘**: 审计者 (Auditor) 必须强制指出提案中的 3 个技术弱点
- **共识收敛**: 必须根据审计意见生成最终的 JSON 规格说明书

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量：
   ```bash
   cp .env.example .env
   # 在 .env 文件中填入你的 API 密钥
   ```

3. 运行框架：
   ```bash
   python main.py
   ```

## 架构概览

```
core/
├── orchestrator.py    # 核心辩论协调器
└── architect.py       # 项目结构生成器
providers/
├── base.py           # 基础提供者类
├── gemini.py         # Google Gemini 提供者
└── zhipu.py          # Zhipu AI 提供者
schema/
└── project.py        # 项目规格数据模型
prompts/
├── system.txt        # 系统提示词
└── architect.txt     # 架构师提示词
output/               # 生成的项目存放目录
```

## 使用场景

- 自动化项目脚手架生成
- 技术方案辩论与优化
- 快速原型开发
- 团队协作辅助工具

## 配置系统

Vibe Nexus 框架支持灵活的AI提供者配置，您可以根据需要配置不同的AI组合：

### 配置文件结构

配置文件位于 `config/ai_config.json`，支持以下参数：

```json
{
  "proposer": {
    "provider": "gemini",      // 提议者提供者 (gemini 或 zhipu)
    "model": "gemini-latest-flash"  // 提议者模型名称
  },
  "auditor": {
    "provider": "zhipu",       // 审计者提供者 (gemini 或 zhipu)
    "model": "glm-4-flash"     // 审计者模型名称
  },
  "fallback_models": {
    "gemini": "gemini-pro",
    "zhipu": "glm-4"
  },
  "api_timeout": 120,
  "retry_attempts": 3
}
```

### 配置说明

框架使用 `config/ai_config.json` 作为默认配置文件，您可以根据需要修改其中的AI提供者和模型配置。

### 自定义配置

您可以创建自己的配置文件，例如让两个AI都使用相同模型进行辩论，或尝试不同的模型组合。

要使用自定义配置，可以修改 `main.py` 中的 Orchestrator 初始化：

```python
# 使用自定义配置
orchestrator = Orchestrator("config/your_custom_config.json")
```