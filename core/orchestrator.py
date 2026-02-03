import asyncio
import json
from typing import Tuple, Dict, Any
from providers.base import BaseProvider
from providers.gemini import GeminiProvider
from providers.zhipu import ZhipuProvider
import re


class Orchestrator:
    """
    核心协调器，实现异步辩论流
    展示两个AI提供者之间的观点博弈
    """
    
    def __init__(self, config_path: str = "config/ai_config.json"):
        # 加载配置文件
        self.config = self._load_config(config_path)

        # 根据配置初始化提供者
        self.proposer = self._initialize_provider(self.config.get("proposer", {}), "proposer")
        self.auditor = self._initialize_provider(self.config.get("auditor", {}), "auditor")

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[WARN] 配置文件 {config_path} 未找到，使用默认配置")
            return {
                "proposer": {"provider": "gemini", "model": "gemini-latest-flash"},
                "auditor": {"provider": "zhipu", "model": "glm-4-flash"},
                "fallback_models": {"gemini": "gemini-pro", "zhipu": "glm-4"},
                "api_timeout": 120,
                "retry_attempts": 3
            }
        except json.JSONDecodeError:
            print(f"[ERROR] 配置文件 {config_path} 格式错误，使用默认配置")
            return {
                "proposer": {"provider": "gemini", "model": "gemini-latest-flash"},
                "auditor": {"provider": "zhipu", "model": "glm-4-flash"},
                "fallback_models": {"gemini": "gemini-pro", "zhipu": "glm-4"},
                "api_timeout": 120,
                "retry_attempts": 3
            }

    def _initialize_provider(self, provider_config: dict, role: str) -> BaseProvider:
        """根据配置初始化提供者"""
        provider_type = provider_config.get("provider", "gemini")
        model = provider_config.get("model")

        try:
            if provider_type.lower() == "gemini":
                from providers.gemini import GeminiProvider
                return GeminiProvider(model=model)
            elif provider_type.lower() == "zhipu":
                from providers.zhipu import ZhipuProvider
                return ZhipuProvider(model=model)
            else:
                print(f"[ERROR] 不支持的提供者类型: {provider_type}")
                return None
        except ValueError as e:
            print(f"[WARN] {role} ({provider_type}) 初始化失败: {e}")
            print(f"[INFO] 请在 .env 文件中设置相应的API密钥")
            return None
        except ImportError as e:
            print(f"[ERROR] 无法导入 {provider_type} 提供者: {e}")
            return None
        
    async def conduct_debate(self, initial_prompt: str) -> Dict[str, Any]:
        """
        进行多轮辩论，包括提议、审计、反馈和共识达成
        遵循辩论准则：冲突挖掘和共识收敛
        实现博弈反馈循环，提升收敛度
        """
        print("🔄 开始AI辩论流程...")
        debate_log = []

        # 检查提供者是否已初始化
        proposer_name = getattr(self.proposer, '__class__', type(None)).__name__.replace('Provider', '')
        auditor_name = getattr(self.auditor, '__class__', type(None)).__name__.replace('Provider', '')

        if not self.proposer and not self.auditor:
            return {
                "final_spec": None,
                "debate_log": [{"error": "两个AI提供者均未初始化，请检查API密钥配置"}],
                "success": False
            }
        elif not self.proposer:
            return {
                "final_spec": None,
                "debate_log": [{"error": f"提议者({proposer_name})未初始化，请检查相应API密钥配置"}],
                "success": False
            }
        elif not self.auditor:
            return {
                "final_spec": None,
                "debate_log": [{"error": f"审计者({auditor_name})未初始化，请检查相应API密钥配置"}],
                "success": False
            }

        print(f"📝 提议者({proposer_name})正在生成初始方案...")
        # 步骤1: 提议者提出初始方案（带重试机制）
        max_retries = 3
        retry_count = 0
        proposal = None

        while retry_count < max_retries:
            proposal = await self.proposer.generate_response(
                f"请为以下需求提供一个详细的解决方案：{initial_prompt}\n\n"
                f"请确保方案包含具体的实施步骤、技术选型和风险评估。"
            )

            if proposal["success"]:
                print("✅ 提议者方案生成成功")
                break
            else:
                retry_count += 1
                print(f"⚠️  提议者生成方案失败，正在重试 ({retry_count}/{max_retries})... 错误: {proposal['error']}")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(2)  # 等待2秒后重试

        if not proposal or not proposal["success"]:
            error_msg = proposal['error'] if proposal else '未知错误'
            # 检查是否是网络连接问题
            if "网络连接问题:" in error_msg or "连接错误:" in error_msg:
                print(f"⚠️  检测到网络连接问题，可能需要检查网络设置")
            return {
                "final_spec": None,
                "debate_log": [{"error": f"提议者生成方案失败: {error_msg}"}],
                "success": False
            }

        debate_log.append({
            "speaker": "proposer",
            "content": proposal["content"],
            "summary": "提出初始方案"
        })

        # 显示初始方案
        print(f"\n📋 提议者初始方案:\n{proposal['content'][:500]}...")  # 只示前500个字符
        print(f"\n🔍 审计者({auditor_name})正在分析方案并指出技术弱点...")
        # 步骤2: 审计者对方案进行审计，强制指出3个技术弱点
        audit_prompt = (
            f"作为技术审计专家，请仔细审查以下技术方案，并严格按照要求指出其中存在的问题：\n\n"
            f"技术方案：\n{proposal['content']}\n\n"
            f"请严格按以下格式提供审计结果：\n"
            f"1. 技术弱点一：[具体问题]\n"
            f"2. 技术弱点二：[具体问题]\n"
            f"3. 技术弱点三：[具体问题]\n"
            f"4. 改进建议：[针对上述问题的改进建议]"
        )

        # 审计者调用（带重试机制）
        max_retries = 3
        retry_count = 0
        audit_result = None

        while retry_count < max_retries:
            audit_result = await self.auditor.generate_response(audit_prompt)

            if audit_result["success"]:
                print("✅ 审计者分析完成")
                break
            else:
                retry_count += 1
                print(f"⚠️  审计者分析方案失败，正在重试 ({retry_count}/{max_retries})... 错误: {audit_result['error']}")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(2)  # 等待2秒后重试

        if not audit_result or not audit_result["success"]:
            return {
                "final_spec": None,
                "debate_log": debate_log + [{"error": f"审计者分析方案失败: {audit_result['error'] if audit_result else '未知错误'}"}],
                "success": False
            }

        debate_log.append({
            "speaker": "auditor",
            "content": audit_result["content"],
            "summary": "指出3个技术弱点"
        })

        # 显示审计结果
        print(f"\n🔍 审计者指出的技术弱点:\n{audit_result['content'][:500]}...")  # 显示前500个字符
        print(f"\n🔄 提议者({proposer_name})正在根据审计意见进行第一轮改进...")
        # 步骤3: 提议者根据审计意见进行第一轮改进
        first_improvement_prompt = (
            f"原始方案：\n{proposal['content']}\n\n"
            f"审计意见：\n{audit_result['content']}\n\n"
            f"请根据审计意见改进原方案，解决指出的问题，同时保持方案的核心功能不变。"
        )

        # 第一次改进（带重试机制）
        max_retries = 3
        retry_count = 0
        first_improved_proposal = None

        while retry_count < max_retries:
            first_improved_proposal = await self.proposer.generate_response(first_improvement_prompt)

            if first_improved_proposal["success"]:
                print("✅ 第一轮改进完成")
                break
            else:
                retry_count += 1
                print(f"⚠️  提议者第一次改进方案失败，正在重试 ({retry_count}/{max_retries})... 错误: {first_improved_proposal['error']}")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(2)  # 等待2秒后重试

        if not first_improved_proposal or not first_improved_proposal["success"]:
            return {
                "final_spec": None,
                "debate_log": debate_log + [{"error": f"提议者第一次改进方案失败: {first_improved_proposal['error'] if first_improved_proposal else '未知错误'}"}],
                "success": False
            }

        debate_log.append({
            "speaker": "proposer",
            "content": first_improved_proposal["content"],
            "summary": "根据审计意见第一次改进方案"
        })

        # 显示改进后的方案
        print(f"\n🔄 提议者改进后的方案:\n{first_improved_proposal['content'][:500]}...")  # 显示前500个字符
        print(f"\n🔍 审计者({auditor_name})正在审核改进后的方案...")
        # 步骤4: 审计者再次审核改进后的方案，提供第二轮反馈
        second_audit_prompt = (
            f"请再次审核以下改进后的技术方案：\n\n"
            f"改进后方案：\n{first_improved_proposal['content']}\n\n"
            f"审计意见：\n{audit_result['content']}\n\n"
            f"请评估改进方案是否已妥善解决之前提出的3个技术弱点，如有未解决的问题，请再次指出并提供进一步的改进建议。"
        )

        # 第二次审核（带重试机制）
        max_retries = 3
        retry_count = 0
        second_audit = None

        while retry_count < max_retries:
            second_audit = await self.auditor.generate_response(second_audit_prompt)

            if second_audit["success"]:
                print("✅ 第二轮审核完成")
                break
            else:
                retry_count += 1
                print(f"⚠️  审计者第二次审核失败，正在重试 ({retry_count}/{max_retries})... 错误: {second_audit['error']}")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(2)  # 等待2秒后重试

        if not second_audit or not second_audit["success"]:
            # 即使第二次审核失败，我们也继续使用第一次改进的结果
            print(f"⚠️  审计者第二次审核失败，使用第一次审核结果: {second_audit['error'] if second_audit else '未知错误'}")
            second_audit = {"content": "第二次审核未能完成，使用第一次审核结果"}
        else:
            debate_log.append({
                "speaker": "auditor",
                "content": second_audit["content"],
                "summary": "第二次审核并提供进一步改进建议"
            })

        # 显示第二轮审核结果
        print(f"\n🔍 审计者第二轮审核结果:\n{second_audit['content'][:500]}...")  # 显示前500个字符
        print(f"\n🔄 提议者({proposer_name})正在根据所有审计意见进行最终方案精炼...")
        # 步骤5: 提议者根据第二轮审计意见进行最终精炼（博弈反馈循环的关键步骤）
        refinement_prompt = (
            f"基于以下信息进行最终方案精炼：\n\n"
            f"初始需求：{initial_prompt}\n\n"
            f"原始方案：\n{proposal['content']}\n\n"
            f"第一次审计意见：\n{audit_result['content']}\n\n"
            f"第一次改进方案：\n{first_improved_proposal['content']}\n\n"
            f"第二次审计意见：\n{second_audit.get('content', '无第二次审计意见')}\n\n"
            f"请综合考虑所有审计意见，生成一个高度优化的最终方案，确保所有技术弱点都得到妥善解决，"
            f"同时保持方案的可行性和完整性。方案应包含具体的实施步骤、技术选型和风险缓解措施。"
        )

        # 方案精炼（带重试机制）
        max_retries = 3
        retry_count = 0
        refined_proposal = None

        while retry_count < max_retries:
            refined_proposal = await self.proposer.generate_response(refinement_prompt)

            if refined_proposal["success"]:
                print("✅ 方案精炼完成")
                break
            else:
                retry_count += 1
                print(f"⚠️  提议者方案精炼失败，正在重试 ({retry_count}/{max_retries})... 错误: {refined_proposal['error']}")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(2)  # 等待2秒后重试

        if not refined_proposal or not refined_proposal["success"]:
            # 如果精炼失败，回退到第一次改进的结果
            print(f"⚠️  提议者方案精炼失败，回退到第一次改进结果: {refined_proposal['error'] if refined_proposal else '未知错误'}")
            refined_proposal_content = first_improved_proposal["content"]
        else:
            refined_proposal_content = refined_proposal["content"]
            debate_log.append({
                "speaker": "proposer",
                "content": refined_proposal_content,
                "summary": "最终精炼方案（吸收所有审计意见）"
            })

        print(f"📝 正在生成最终的JSON规格说明书...")
        # 步骤6: 生成最终的JSON规格说明书（共识收敛）
        # 使用精炼后的方案生成最终规格，确保已吸收所有审计意见
        consensus_prompt = (
            f"基于以下完整的辩论过程，生成最终的JSON格式项目规格说明书：\n\n"
            f"初始需求：{initial_prompt}\n\n"
            f"原始方案：{proposal['content']}\n\n"
            f"第一次审计意见：{audit_result['content']}\n\n"
            f"第一次改进方案：{first_improved_proposal['content']}\n\n"
            f"第二次审计意见：{second_audit.get('content', '无第二次审计意见')}\n\n"
            f"最终精炼方案：{refined_proposal_content}\n\n"
            "请生成符合以下JSON结构的规格说明书：\n"
            "{\n"
            '  "project_name": "...",\n'
            '  "description": "...",\n'
            '  "version": "1.0.0",\n'
            '  "architecture_proposal": "...",\n'
            '  "tasks": [\n'
            "    {\n"
            '      "id": 1,\n'
            '      "title": "...",\n'
            '      "description": "...",\n'
            '      "technical_requirement": "...",\n'
            '      "target_path": "...",\n'
            '      "verification": "...",\n'
            '      "flexibility": "fixed" \n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "注意：\n"
            "1. 必须严格遵循PnC准则，每个任务都必须包含target_path（物理路径）和verification（验证步骤）。\n"
            "2. architecture_proposal字段必须包含整体架构设计方案，包括目录划分理由、技术选型决策树、设计模式、核心算法逻辑等。\n"
            "3. 每个任务的technical_requirement字段必须包含具体的技术实现细节和约束，如使用的锁、数据结构、错误处理逻辑等。\n"
            "4. 每个任务的flexibility字段必须设置为'fixed'或'flexible'之一，表示实现的灵活性程度。\n"
            "5. 优先在architecture_proposal中定义抽象基类或接口协议。"
        )

        # 生成最终规格（带重试机制）
        max_retries = 3
        retry_count = 0
        final_spec_result = None

        while retry_count < max_retries:
            final_spec_result = await self.proposer.generate_response(consensus_prompt)

            if final_spec_result["success"]:
                print("✅ 最终规格说明书生成完成")
                break
            else:
                retry_count += 1
                print(f"⚠️  生成最终规格说明失败，正在重试 ({retry_count}/{max_retries})... 错误: {final_spec_result['error']}")
                if retry_count < max_retries:
                    import asyncio
                    await asyncio.sleep(2)  # 等待2秒后重试

        if not final_spec_result or not final_spec_result["success"]:
            return {
                "final_spec": None,
                "debate_log": debate_log + [{"error": f"生成最终规格说明失败: {final_spec_result['error'] if final_spec_result else '未知错误'}"}],
                "success": False
            }

        # 尝试解析最终规格说明为JSON
        final_spec = self._extract_json_from_response(final_spec_result["content"])

        # 显示最终规格说明书
        print(f"\n📋 最终JSON规格说明书:\n{final_spec_result['content'][:1000]}...")  # 显示前1000个字符

        debate_log.append({
            "speaker": "consensus",
            "content": final_spec_result["content"],
            "summary": "生成最终JSON规格说明书（已吸收所有审计意见）"
        })

        return {
            "final_spec": final_spec,
            "debate_log": debate_log,
            "success": True
        }
    
    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """
        从AI响应中提取JSON内容
        """
        # 首先检查是否包含markdown代码块标记
        import re
        # 查找 ```json ... ``` 代码块
        json_match = re.search(r'```(?:json)?\s*(.+?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        # 查找JSON对象
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx == -1 or end_idx == -1:
            return {"error": "无法从响应中找到有效的JSON对象", "raw_response": text}

        json_str = text[start_idx:end_idx+1]

        try:
            data = json.loads(json_str)

            # 确保 architecture_proposal 是字符串
            if "architecture_proposal" in data:
                if isinstance(data["architecture_proposal"], dict):
                    data["architecture_proposal"] = json.dumps(data["architecture_proposal"], ensure_ascii=False)
                elif not isinstance(data["architecture_proposal"], str):
                    data["architecture_proposal"] = str(data["architecture_proposal"])

            # 确保每个任务的 technical_requirement 是字符串
            if "tasks" in data:
                for task in data["tasks"]:
                    if "technical_requirement" in task:
                        if isinstance(task["technical_requirement"], dict):
                            task["technical_requirement"] = json.dumps(task["technical_requirement"], ensure_ascii=False)
                        elif not isinstance(task["technical_requirement"], str):
                            task["technical_requirement"] = str(task["technical_requirement"])

                    # 确保 verification 是字符串（如果它是列表，则合并为字符串）
                    if "verification" in task:
                        if isinstance(task["verification"], list):
                            task["verification"] = "; ".join(str(item) for item in task["verification"])
                        elif not isinstance(task["verification"], str):
                            task["verification"] = str(task["verification"])

            return data
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析失败: {str(e)}", "raw_response": json_str}
    
    async def run_single_round_debate(self, topic: str) -> Dict[str, Any]:
        """
        运行多轮辩论（包含博弈反馈循环）
        """
        return await self.conduct_debate(topic)