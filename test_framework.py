"""
Vibe Nexus 框架测试脚本
用于验证框架各组件的功能
"""
import asyncio
import json
from pathlib import Path

from core.orchestrator import Orchestrator
from core.architect import Architect
from schema.project import ProjectSpec, Task


def test_project_schema():
    """测试项目模式定义"""
    print("[TEST] 测试项目模式定义...")

    # 创建一个示例任务
    task = Task(
        id=1,
        title="创建主页面",
        description="创建应用程序的主页面",
        target_path="src/main_page.py",
        verification="页面能够正常加载且无错误"
    )

    # 创建一个示例项目规格
    project_spec = ProjectSpec(
        project_name="TestProject",
        description="这是一个测试项目",
        tasks=[task]
    )

    print(f"[PASS] 项目名称: {project_spec.project_name}")
    print(f"[PASS] 任务数量: {len(project_spec.tasks)}")
    print()


def test_architect():
    """测试架构师功能"""
    print("[TEST] 测试架构师功能...")

    # 创建一个示例项目规格
    sample_spec = {
        "project_name": "UnitTestProject",
        "description": "用于单元测试的项目",
        "version": "1.0.0",
        "tasks": [
            {
                "id": 1,
                "title": "创建主页面",
                "description": "创建应用程序的主页面",
                "target_path": "src/main.py",
                "verification": "页面能够正常加载且无错误"
            },
            {
                "id": 2,
                "title": "创建样式文件",
                "description": "创建应用程序的CSS样式",
                "target_path": "src/style.css",
                "verification": "样式能够正确应用到页面元素"
            },
            {
                "id": 3,
                "title": "创建文档",
                "description": "创建项目文档",
                "target_path": "docs/readme.md",
                "verification": "文档内容完整且格式正确"
            }
        ]
    }

    architect = Architect("test_output")
    success = architect.create_project_structure(sample_spec)

    if success:
        print("[PASS] 项目结构创建成功!")
        project_path = Path("test_output") / "UnitTestProject"
        print(f"[INFO] 项目位置: {project_path.absolute()}")

        # 验证创建的目录结构
        expected_dirs = ["src", "tests", "docs", "config", "scripts"]
        for dir_name in expected_dirs:
            dir_path = project_path / dir_name
            if dir_path.exists():
                print(f"[PASS] 目录存在: {dir_name}/")
            else:
                print(f"[FAIL] 目录缺失: {dir_name}/")

        # 验证创建的文件
        expected_files = [
            "README.md",
            "config/project.json",
            "src/main.py",
            "src/style.css",
            "docs/readme.md"
        ]

        for file_path in expected_files:
            full_path = project_path / file_path
            if full_path.exists():
                print(f"[PASS] 文件存在: {file_path}")
            else:
                print(f"[FAIL] 文件缺失: {file_path}")
    else:
        print("[FAIL] 项目结构创建失败!")

    print()


def test_orchestrator_initialization():
    """测试协调器初始化"""
    print("[TEST] 测试协调器初始化...")

    orchestrator = Orchestrator()

    if orchestrator.proposer is None:
        print("[WARN] 提议者未初始化 (预期行为，因为没有API密钥)")
    else:
        print("[PASS] 提议者已初始化")

    if orchestrator.auditor is None:
        print("[WARN] 审计者未初始化 (预期行为，因为没有API密钥)")
    else:
        print("[PASS] 审计者已初始化")

    print()


async def run_tests():
    """运行所有测试"""
    print(">>> 开始运行 Vibe Nexus 框架测试...\n")
    
    test_project_schema()
    test_architect()
    test_orchestrator_initialization()
    
    print("[DONE] 所有测试完成!")


if __name__ == "__main__":
    asyncio.run(run_tests())