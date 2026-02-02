#!/usr/bin/env python3
"""
Vibe Coding 架构师 Agent 测试脚本
用于验证系统功能是否正常
"""

import sys
import os
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("[测试] 测试模块导入...")
    
    try:
        from schema.project import ProjectSpec, Task
        print("[OK] schema.project 模块导入成功")
    except ImportError as e:
        print(f"[ERROR] schema.project 导入失败: {e}")
        return False
    
    return True

def test_models():
    """测试 Pydantic 模型"""
    print("\n[测试] 测试 Pydantic 模型...")
    
    try:
        from schema.project import ProjectSpec, Task
        from datetime import datetime
        
        # 测试 Task 模型
        task = Task(
            id="test_001",
            title="测试任务",
            description="这是一个测试任务",
            target_path="output/test_project/src/main.py",
            verification="验收标准：文件存在且包含测试代码"
        )
        print("[OK] Task 模型创建成功")
        
        # 测试 ProjectSpec 模型
        project = ProjectSpec(
            id="proj_test",
            name="测试项目",
            description="这是一个测试项目",
            author="测试用户",
            root_directory="output/test_project",
            tasks=[task],
            tech_stack={"python": "3.9"},
            dependencies={"pydantic": "^2.5.0"}
        )
        print("[OK] ProjectSpec 模型创建成功")
        
        # 测试模型方法
        found_task = project.get_task_by_id("test_001")
        if found_task and found_task.id == "test_001":
            print("[OK] get_task_by_id 方法工作正常")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 模型测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n[测试] 测试文件结构...")
    
    required_files = [
        "schema/project.py",
        "prompts/system.txt",
        "prompts/architect.txt",
        "main.py",
        "requirements.txt",
        ".env.example",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path} 存在")
        else:
            print(f"[ERROR] {file_path} 不存在")
            all_exist = False
    
    return all_exist

def test_prompt_files():
    """测试提示文件内容"""
    print("\n[测试] 测试提示文件内容...")
    
    try:
        # 检查系统提示
        with open("prompts/system.txt", 'r', encoding='utf-8') as f:
            system_content = f.read()
        
        if "禁止根目录污染" in system_content:
            print("[OK] system.txt 包含核心原则")
        else:
            print("[ERROR] system.txt 缺少核心原则")
            return False
        
        # 检查架构师提示
        with open("prompts/architect.txt", 'r', encoding='utf-8') as f:
            architect_content = f.read()
        
        if "target_path" in architect_content and "verification" in architect_content:
            print("[OK] architect.txt 包含必要字段")
        else:
            print("[ERROR] architect.txt 缺少必要字段")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 提示文件测试失败: {e}")
        return False

def test_main_module():
    """测试主模块"""
    print("\n[测试] 测试主模块...")
    
    try:
        # 检查 main.py 是否可以导入（需要环境变量）
        if os.getenv("SKIP_MAIN_TEST"):
            print("[SKIP] 跳过主模块测试（需要 API 密钥）")
            return True
        
        # 这里只是测试语法，不实际调用 API
        import ast
        
        with open("main.py", 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        print("[OK] main.py 语法正确")
        
        # 检查关键函数是否存在
        tree = ast.parse(source)
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        required_functions = ["main", "run", "parse_user_requirement", "create_project_structure"]
        for func in required_functions:
            if func in functions:
                print(f"[OK] 函数 {func} 存在")
            else:
                print(f"[ERROR] 函数 {func} 不存在")
                return False
        
        return True
        
    except SyntaxError as e:
        print(f"[ERROR] main.py 语法错误: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 主模块测试失败: {e}")
        return False

def run_tests():
    """运行所有测试"""
    print("[START] Vibe Coding 架构师 Agent 测试开始\n")
    
    tests = [
        test_imports,
        test_models,
        test_file_structure,
        test_prompt_files,
        test_main_module
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n[RESULT] 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("[SUCCESS] 所有测试通过！系统已准备就绪。")
        print("\n[USAGE] 使用说明:")
        print("1. 设置环境变量: cp .env.example .env")
        print("2. 编辑 .env 文件添加 OPENAI_API_KEY")
        print("3. 安装依赖: pip install -r requirements.txt")
        print("4. 运行程序: python main.py \"你的项目需求\"")
        return True
    else:
        print("[ERROR] 部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)