# Vibe Coding 架构师 Agent

🏗️ **智能项目架构设计工具** - 自动化项目结构创建、代码占位生成和规格文档编写的 AI 驱动工具。

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![License](https://img.shields.io/badge/license-MIT-purple)

## ✨ 核心特性

- 🧠 **AI 驱动的架构设计** - 基于 OpenAI GPT 的智能项目分析
- 📁 **严格的目录管理** - 遵循"禁止根目录污染"原则
- 🔧 **自动化代码生成** - 根据任务自动创建代码占位文件
- 📋 **结构化任务管理** - Pydantic 模型确保数据完整性
- 🌐 **跨平台兼容** - 使用 pathlib 处理路径，支持 Windows/Linux/Mac
- 📝 **文档自动生成** - 自动生成 SPEC.md 和任务配置

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd vibe_factory

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 OpenAI API Key
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行架构师

```bash
# 直接提供需求
python main.py "创建一个基于 FastAPI 的 REST API 项目，包含用户管理和JWT认证"

# 从文件读取需求
python main.py --file requirements.txt

# 交互式输入需求
python main.py --interactive

# 查看帮助
python main.py --help
```

## 📁 项目结构

```
vibe_factory/
├── schema/
│   └── project.py              # Pydantic 数据模型定义
├── prompts/
│   ├── system.txt              # AI 架构师人格设定
│   └── architect.txt           # JSON 输出格式模板
├── output/                     # 项目输出目录（git忽略）
│   └── your_project/           # 自动生成的项目
│       ├── SPEC.md             # 项目规格文档
│       ├── tasks.json          # 任务配置文件
│       └── src/                # 源代码目录
├── main.py                     # 主程序入口
├── test.py                     # 系统测试脚本
├── requirements.txt            # Python 依赖
├── .env.example               # 环境变量模板
├── .gitignore                  # Git 忽略规则
└── README.md                   # 项目文档
```

## 🎯 使用示例

### 输入需求示例：
```
创建一个用户管理系统，包含以下功能：
1. 用户注册和登录
2. JWT 认证
3. 用户信息管理（CRUD）
4. 权限管理（管理员/普通用户）
使用 FastAPI + SQLAlchemy + PostgreSQL
```

### 自动生成的输出：
- ✅ **完整项目目录结构**
- ✅ **详细的 SPEC.md 规格文档**
- ✅ **tasks.json 任务配置**
- ✅ **代码占位文件和模板**
- ✅ **依赖配置文件**

## 🏛️ 架构设计原则

### 核心原则
1. **禁止根目录污染** - 所有输出必须在 `output/` 项目子目录下
2. **路径严格性** - 使用跨平台兼容的完整路径
3. **验收导向设计** - 每个任务都有明确的 `verification` 验收标准
4. **依赖管理** - 任务间依赖关系清晰明确

### AI 架构师人格
- **系统性思维** - 从整体架构角度思考问题
- **严谨细致** - 对路径、依赖、接口要求严格
- **前瞻性** - 考虑可维护性和扩展性
- **责任感** - 对架构决策负责

## 📊 数据模型

### ProjectSpec 模型
```python
class ProjectSpec(BaseModel):
    id: str                    # 项目唯一标识
    name: str                  # 项目名称
    description: str           # 项目描述
    version: str               # 版本号
    author: str                # 作者
    root_directory: str        # 项目根目录
    tasks: List[Task]         # 任务列表
    tech_stack: Dict[str, str] # 技术栈配置
    dependencies: Dict[str, str] # 项目依赖
    config: Dict[str, Any]    # 配置信息
    metadata: Dict[str, Any]  # 元数据
```

### Task 模型
```python
class Task(BaseModel):
    id: str                    # 任务唯一标识
    title: str                 # 任务标题
    description: str           # 任务描述
    target_path: str           # 🎯 强制路径（必需）
    verification: str          # ✅ 验收标准（必需）
    dependencies: List[str]    # 依赖任务ID
    priority: str              # 优先级（high/medium/low）
    status: str                # 状态（pending/in_progress/completed）
    metadata: Dict[str, Any]   # 元数据
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API 密钥 |
| `OPENAI_BASE_URL` | ❌ | `https://api.openai.com/v1` | API 基础 URL |
| `OPENAI_MODEL` | ❌ | `gpt-4-turbo-preview` | 使用的模型 |
| `PROJECT_OUTPUT_DIR` | ❌ | `output` | 项目输出目录 |

### requirements.txt 主要依赖
```
openai>=1.6.0              # OpenAI SDK
pydantic>=2.5.0            # 数据验证
```

## 🧪 测试验证

运行测试脚本验证系统完整性：

```bash
python test.py
```

测试覆盖：
- ✅ 模块导入测试
- ✅ Pydantic 模型验证
- ✅ 文件结构检查
- ✅ 提示文件内容验证
- ✅ 主程序语法检查

## 🔧 开发指南

### 添加新的代码模板

在 `main.py` 的 `_generate_stub_content` 方法中添加新扩展名支持：

```python
elif ext == '.your_ext':
    return f"""# {task.title}
# {task.description}
# 验收标准: {task.verification}

# TODO: 实现具体内容
"""
```

### 自定义架构师人格

编辑 `prompts/system.txt` 文件来修改 AI 的行为原则和工作流程。

### 扩展功能

1. **添加新的验证规则** - 在 Pydantic 模型中添加自定义验证器
2. **集成其他 AI 模型** - 扩展 API 调用逻辑
3. **添加模板引擎** - 使用 Jinja2 等模板引擎生成更复杂的代码

## 🐛 故障排除

### 常见问题

**Q: API 调用失败**
```
A: 检查 .env 文件中的 OPENAI_API_KEY 是否正确设置
```

**Q: 编码错误**
```
A: 确保使用 UTF-8 编码，特别是在 Windows 系统上
```

**Q: 路径错误**
```
A: 检查 prompts/ 目录下的文件是否存在
```

**Q: 依赖安装失败**
```
A: 尝试升级 pip: pip install --upgrade pip
```

## 🤝 贡献指南

1. **Fork** 项目到你的 GitHub
2. **创建** 功能分支: `git checkout -b feature/amazing-feature`
3. **提交** 更改: `git commit -m 'Add amazing feature'`
4. **推送** 到分支: `git push origin feature/amazing-feature`
5. **创建** Pull Request

### 代码规范

- 使用 **Black** 进行代码格式化
- 遵循 **PEP 8** 编码规范
- 添加适当的 **类型提示**
- 编写 **单元测试**

## 📄 许可证

本项目采用 **MIT 许可证** - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供强大的 AI 能力
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 优秀的数据验证库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架

## 📞 联系方式

- 📧 **Issues**: [GitHub Issues](https://github.com/your-username/vibe_factory/issues)
- 🐦 **Twitter**: [@your-twitter](https://twitter.com/your-twitter)
- 💬 **Discord**: [加入讨论](https://discord.gg/your-server)

---

<div align="center">
  <strong>🏗️ 让 AI 为你构建完美的项目架构！</strong><br>
  <em>Made with ❤️ by Vibe Coding Team</em>
</div>