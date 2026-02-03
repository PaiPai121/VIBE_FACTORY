# Vibe Nexus 核心宪法

## 第一部分：框架开发约束 (Meta Rules)
- **模块化驱动**: 所有 Provider (Gemini/GLM) 必须继承自 Base 类，严禁硬编码。
- **环境变量感知**: 严禁在代码中硬编码 API Key，必须通过 `.env` 读取。
- **鲁棒性**: 必须处理网络超时和 JSON 解析失败的情况，提供降级输出。

## 第二部分：架构生成约束 (Architecture Rules)
- **目录隔离**: 业务代码必须存在于 `output/项目名/src` 目录下，严禁污染根目录。
- **协议先行**: 模块间通信必须定义明确的数据模型 (Pydantic/Interface)。
- **PnC 准则**: 所有任务 (Tasks) 必须包含物理路径 (`target_path`) 和可执行的验证步骤 (`verification`)。

## 第三部分：辩论准则 (Debate Rules)
- **冲突挖掘**: 审计者 (Auditor) 必须强制指出提案中的 3 个技术弱点。
- **共识收敛**: 必须根据审计意见生成最终的 JSON 规格说明书。