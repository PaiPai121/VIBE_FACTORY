import asyncio
import os
from core.orchestrator import Orchestrator
from core.architect import Architect
from schema.project import ProjectSpec
import json

# 初始化日志系统
try:
    from utils.logging_utils import setup_logging
    setup_logging()
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)


def print_constitution_principles():
    """
    打印宪法中的核心原则
    """
    constitution = """
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
"""
    print(constitution)
    print("\n" + "="*60 + "\n")


async def main():
    """
    主函数，启动 Vibe Nexus 框架
    """
    print_constitution_principles()
    
    print("欢迎使用 Vibe Nexus 框架!")
    print("正在初始化系统...\n")
    
    # 初始化核心组件
    orchestrator = Orchestrator("config/default_config.json")  # 使用双Zhipu配置文件
    architect = Architect()
    
    print("系统初始化完成!\n")
    
    while True:
        print("请选择操作:")
        print("1. 开始新项目设计")
        print("2. 退出")
        
        choice = input("\n请输入选择 (1 或 2): ").strip()
        
        if choice == "1":
            print("\n请输入项目需求描述:")
            print("提示：可以输入多行内容，输入单独一行'END'结束输入")
            print("例如：创建一个Python Flask应用")
            print("      包含用户认证和数据存储功能")
            print("      需要支持RESTful API")
            print("      END")
            print(">")

            try:
                # 尝试读取多行输入
                lines = []
                while True:
                    line = input()
                    if line.strip() == 'END':
                        break
                    lines.append(line)

                project_description = '\n'.join(lines)
            except EOFError:
                # 如果在非交互环境中运行，则使用单行输入
                project_description = input("单行输入项目需求: ")

            if not project_description.strip():
                print("项目需求不能为空，请重新输入。\n")
                continue
                
            print("\n正在进行AI辩论设计过程...")
            # 根据实际配置显示提供者信息
            proposer_name = getattr(orchestrator.proposer, '__class__', type(None)).__name__.replace('Provider', '') if orchestrator.proposer else 'Unknown'
            auditor_name = getattr(orchestrator.auditor, '__class__', type(None)).__name__.replace('Provider', '') if orchestrator.auditor else 'Unknown'
            proposer_model = getattr(orchestrator.proposer, 'model', 'Unknown') if orchestrator.proposer else 'Unknown'
            auditor_model = getattr(orchestrator.auditor, 'model', 'Unknown') if orchestrator.auditor else 'Unknown'
            print(f"提議者({proposer_name}:{proposer_model})和審計者({auditor_name}:{auditor_model})正在討論最佳方案...\n")
            
            # 运行辩论流程
            debate_result = await orchestrator.run_single_round_debate(project_description)

            if debate_result["success"]:
                final_spec = debate_result["final_spec"]

                if final_spec and "error" not in final_spec:
                    print("✅ 辩论设计完成! 生成的项目规格:")
                    print(json.dumps(final_spec, ensure_ascii=False, indent=2))

                    print("\n是否要根据此规格创建项目文件? (y/n)")
                    confirm = input("> ").strip().lower()

                    if confirm in ['y', 'yes', '是']:
                        print("\n正在创建项目结构...")
                        success = architect.create_project_structure(final_spec)

                        if success:
                            print(f"\n🎉 项目 {final_spec.get('project_name', 'Unknown')} 创建成功!")
                            print(f"项目位置: output/{final_spec.get('project_name', 'Unknown')}/")
                        else:
                            print("\n❌ 项目创建失败!")
                    else:
                        print("\n跳过项目创建步骤。")
                else:
                    print(f"❌ 生成项目规格失败: {final_spec.get('error', '未知错误')}")
                    if 'raw_response' in final_spec:
                        print(f"原始响应: {final_spec['raw_response'][:200]}...")
            else:
                print("❌ 辩论设计过程失败!")
                has_network_error = False
                for log_entry in debate_result.get("debate_log", []):
                    if "error" in log_entry:
                        error_msg = log_entry['error']
                        print(f"錯誤: {error_msg}")
                        # 检查是否是网络连接错误
                        if "网络连接问题:" in error_msg or "连接错误:" in error_msg or "timeout" in error_msg.lower():
                            has_network_error = True

                # 如果是网络错误，提供诊断选项
                if has_network_error:
                    print("\n💡 检测到网络连接问题，是否要运行网络诊断工具? (y/n)")
                    diag_choice = input("> ").strip().lower()
                    if diag_choice in ['y', 'yes', '是']:
                        try:
                            from utils.network_diagnostic import diagnose_network_issues
                            await asyncio.get_event_loop().run_in_executor(None, diagnose_network_issues)
                        except ImportError:
                            print("⚠️  无法找到网络诊断工具")

                # 询问用户是否重试
                print("\n是否要重试辩论过程? (y/n)")
                retry_choice = input("> ").strip().lower()

                if retry_choice in ['y', 'yes', '是']:
                    print("\n正在重试辩论设计过程...")
                    debate_result = await orchestrator.run_single_round_debate(project_description)

                    if debate_result["success"]:
                        final_spec = debate_result["final_spec"]

                        if final_spec and "error" not in final_spec:
                            print("✅ 重试成功! 生成的项目规格:")
                            print(json.dumps(final_spec, ensure_ascii=False, indent=2))

                            print("\n是否要根据此规格创建项目文件? (y/n)")
                            confirm = input("> ").strip().lower()

                            if confirm in ['y', 'yes', '是']:
                                print("\n正在创建项目结构...")
                                success = architect.create_project_structure(final_spec)

                                if success:
                                    print(f"\n🎉 项目 {final_spec.get('project_name', 'Unknown')} 创建成功!")
                                    print(f"项目位置: output/{final_spec.get('project_name', 'Unknown')}/")
                                else:
                                    print("\n❌ 项目创建失败!")
                            else:
                                print("\n跳过项目创建步骤。")
                        else:
                            print(f"❌ 重试后仍生成项目规格失败: {final_spec.get('error', '未知错误')}")
                    else:
                        print("❌ 重试辩论设计过程仍然失败!")
                        for log_entry in debate_result.get("debate_log", []):
                            if "error" in log_entry:
                                print(f"錯誤: {log_entry['error']}")
                else:
                    print("跳过重试。")

            print("\n" + "-"*60 + "\n")
            
        elif choice == "2":
            print("\n感谢使用 Vibe Nexus 框架，再见!")
            break
        else:
            print("\n无效选择，请重新输入。\n")


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())