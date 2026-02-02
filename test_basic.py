#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Coding 架构师 Agent - 简化测试版
直接生成一个测试项目
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 导入本地模块
try:
    from schema.project import ProjectSpec, Task
except ImportError:
    print("错误: 无法导入必要模块")
    sys.exit(1)


def create_test_project():
    """创建一个测试项目"""
    print("[START] 创建测试项目...")
    
    # 创建项目规格
    tasks = [
        Task(
            id="task_001",
            title="项目初始化",
            description="创建项目基础结构和配置文件",
            target_path="test_project/README.md",
            verification="验收标准：README.md 文件存在且包含项目描述",
            priority="high",
            status="pending"
        ),
        Task(
            id="task_002",
            title="主程序文件",
            description="创建主程序入口文件",
            target_path="test_project/main.py",
            verification="验收标准：main.py文件存在且包含基本结构",
            dependencies=["task_001"],
            priority="high",
            status="pending"
        ),
        Task(
            id="task_003",
            title="配置文件",
            description="创建项目配置文件",
            target_path="test_project/config.py",
            verification="验收标准：config.py文件存在且包含基本配置",
            dependencies=["task_001"],
            priority="medium",
            status="pending"
        )
    ]
    
    project_spec = ProjectSpec(
        project_name="test_project",
        description="这是一个测试项目，验证系统功能",
        tasks=tasks,
        author="测试用户",
        tech_stack={"language": "python", "framework": "无"},
        config={}
    )
    
    # 创建项目目录
    project_root = Path("output") / "test_project"
    project_root.mkdir(parents=True, exist_ok=True)
    print(f"[OK] 创建项目目录: {project_root}")
    
    # 创建子目录
    (project_root / "config").mkdir(exist_ok=True)
    print("[OK] 创建配置目录")
    
    # 生成 SPEC.md
    spec_file = project_root / "SPEC.md"
    spec_content = f"""# {project_spec.project_name} 项目规格

## 基本信息
- **项目名称**: {project_spec.project_name}
- **描述**: {project_spec.description}
- **作者**: {project_spec.author}
- **创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 技术栈
"""
    
    if project_spec.tech_stack:
        for tech, value in project_spec.tech_stack.items():
            spec_content += f"- **{tech}**: {value}\n"
    
    spec_content += f"""
## 任务列表 ({len(project_spec.tasks)} 个任务)

"""
    
    for i, task in enumerate(project_spec.tasks, 1):
        spec_content += f"### {i}. {task.title}\n"
        spec_content += f"- **ID**: {task.id}\n"
        spec_content += f"- **优先级**: {task.priority}\n"
        spec_content += f"- **状态**: {task.status}\n"
        spec_content += f"- **目标路径**: `{task.target_path}`\n"
        spec_content += f"- **依赖**: {', '.join(task.dependencies) if task.dependencies else '无'}\n"
        spec_content += f"- **描述**: {task.description}\n"
        spec_content += f"- **验收标准**: {task.verification}\n\n"
    
    spec_content += """---
*此文档由 Vibe Coding 架构师 Agent 自动生成*
"""
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print(f"[OK] 生成项目规格文档: {spec_file}")
    
    # 创建代码占位文件
    for task in project_spec.tasks:
        target_file = project_root / task.target_path
        
        # 确保目录存在
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成占位内容
        if target_file.suffix == '.py':
            content = f'''"""
{task.title}

任务ID: {task.id}
描述: {task.description}
验收标准: {task.verification}
创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

def main():
    """主函数 - 待实现"""
    pass

if __name__ == "__main__":
    main()
'''
        elif target_file.suffix == '.md':
            content = f"""# {task.title}

{task.description}

## 待实现内容

- [ ] 实现核心功能
- [ ] 添加测试
- [ ] 完善文档

## 验收标准
{task.verification}

---
*创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        else:
            content = f"""// {task.title}
// 描述: {task.description}
// 验收标准: {task.verification}

// TODO: 请根据项目需求实现具体内容
"""
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] 创建代码占位文件: {target_file}")
    
    # 生成任务JSON文件
    tasks_file = project_root / "tasks.json"
    tasks_data = {
        "generated_at": datetime.now().isoformat(),
        "tasks": [task.model_dump() for task in project_spec.tasks]
    }
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] 生成任务配置文件: {tasks_file}")
    
    print(f"\n[SUCCESS] 测试项目创建完成!")
    print(f"[PATH] 项目路径: {project_root}")
    print(f"[TASKS] 任务数量: {len(project_spec.tasks)}")
    print(f"[FILES] 创建文件数: {len(project_spec.tasks) + 2}")
    
    return project_spec


if __name__ == "__main__":
    try:
        project_spec = create_test_project()
        print(f"\n[COMPLETE] 项目 '{project_spec.project_name}' 创建完成!")
    except Exception as e:
        print(f"[ERROR] 创建失败: {e}")
        sys.exit(1)