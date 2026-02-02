#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 Vibe Coding 架构师 Agent - 主程序
不依赖外部 API，使用本地逻辑生成项目架构
支持交互式输入
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from pydantic import BaseModel
except ImportError as e:
    print(f"请安装必要的依赖: pip install pydantic")
    print(f"导入错误: {e}")
    sys.exit(1)

# 导入本地模块
try:
    from schema.project import ProjectSpec, Task
    from interactive import InteractiveCollector
except ImportError:
    print("错误: 无法导入必要模块")
    sys.exit(1)


class VibeArchitect:
    """Vibe Coding 架构师 Agent 主类"""
    
    def __init__(self):
        """初始化架构师"""
        self.output_base = Path("output")
        
    def parse_user_requirement(self, requirement: str) -> ProjectSpec:
        """解析用户需求并生成项目规格"""
        # 解析需求中的关键信息
        project_info = self._analyze_requirement(requirement)
        
        # 生成基础任务
        tasks = self._generate_tasks(project_info)
        
        # 创建 ProjectSpec 对象
        return ProjectSpec(
            project_name=project_info.get("name", "未命名项目"),
            description=project_info.get("description", requirement),
            tasks=tasks,
            author=project_info.get("author", "开发者"),
            tech_stack=project_info.get("tech_stack", {}),
            config={"output_dir": "output"}
        )
    
    def _analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """分析需求，提取关键信息"""
        lower_req = requirement.lower()
        
        # 项目类型检测
        project_types = {
            "web": ["web", "网站", "website", "frontend", "前端"],
            "api": ["api", "后端", "backend", "rest", "graphql"],
            "mobile": ["mobile", "app", "移动", "手机", "app应用"],
            "cli": ["cli", "命令行", "工具", "tool"],
            "desktop": ["desktop", "桌面", "gui", "客户端"],
            "data": ["data", "数据", "分析", "analytics", "machine learning", "ai"]
        }
        
        detected_type = "general"
        for ptype, keywords in project_types.items():
            if any(keyword in lower_req for keyword in keywords):
                detected_type = ptype
                break
        
        # 技术栈检测
        tech_stack = {}
        
        # 编程语言检测
        languages = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "node"],
            "typescript": ["typescript", "ts"],
            "java": ["java"],
            "go": ["golang", "go"],
            "rust": ["rust"],
            "c++": ["c++", "cpp"],
            "c#": ["c#", "csharp"]
        }
        
        for lang, keywords in languages.items():
            if any(keyword in lower_req for keyword in keywords):
                tech_stack["language"] = lang
                break
        
        # 框架检测
        frameworks = {
            "fastapi": ["fastapi"],
            "django": ["django"],
            "flask": ["flask"],
            "react": ["react"],
            "vue": ["vue"],
            "angular": ["angular"],
            "spring": ["spring"],
            "express": ["express"]
        }
        
        for framework, keywords in frameworks.items():
            if any(keyword in lower_req for keyword in keywords):
                tech_stack["framework"] = framework
                break
        
        # 数据库检测
        databases = ["mysql", "postgresql", "mongodb", "sqlite", "redis"]
        for db in databases:
            if db in lower_req:
                tech_stack["database"] = db
                break
        
        # 提取项目名称（简单处理）
        name = "未命名项目"
        lines = requirement.split('\n')
        for line in lines:
            if '项目名称' in line or 'project' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    name = parts[1].strip()
                    break
        
        return {
            "name": name,
            "description": requirement,
            "type": detected_type,
            "tech_stack": tech_stack,
            "author": "开发者"
        }
    
    def _generate_tasks(self, project_info: Dict[str, Any]) -> List[Task]:
        """根据项目信息生成任务"""
        project_type = project_info.get("type", "general")
        tech_stack = project_info.get("tech_stack", {})
        project_name = project_info.get("name", "未命名项目")
        
        tasks = []
        task_id = 1
        
        # 基础任务
        tasks.append(Task(
            id=f"task_{task_id:03d}",
            title="项目初始化",
            description="创建项目基础结构和配置文件",
            target_path=f"{project_name}/README.md",
            verification="验收标准：README.md 文件存在且包含项目描述",
            priority="high",
            status="pending"
        ))
        task_id += 1
        
        # 根据项目类型添加特定任务
        if project_type == "web":
            tasks.extend([
                Task(
                    id=f"task_{task_id:03d}",
                    title="前端页面结构",
                    description="创建基本的HTML/CSS/JS文件结构",
                    target_path=f"{project_name}/src/index.html",
                    verification="验收标准：HTML文件存在且包含基本页面结构",
                    dependencies=[f"task_{task_id-1:03d}"],
                    priority="high",
                    status="pending"
                ),
                Task(
                    id=f"task_{task_id+1:03d}",
                    title="样式文件",
                    description="创建CSS样式文件",
                    target_path=f"{project_name}/src/style.css",
                    verification="验收标准：CSS文件存在且包含基本样式",
                    dependencies=[f"task_{task_id:03d}"],
                    priority="medium",
                    status="pending"
                )
            ])
            task_id += 2
            
        elif project_type == "api":
            tasks.extend([
                Task(
                    id=f"task_{task_id:03d}",
                    title="API 主文件",
                    description="创建API服务主文件",
                    target_path=f"{project_name}/app.py",
                    verification="验收标准：app.py文件存在且包含基本路由结构",
                    dependencies=[f"task_{task_id-1:03d}"],
                    priority="high",
                    status="pending"
                ),
                Task(
                    id=f"task_{task_id+1:03d}",
                    title="API 路由定义",
                    description="定义API路由和端点",
                    target_path=f"{project_name}/routes.py",
                    verification="验收标准：routes.py文件存在且包含路由定义",
                    dependencies=[f"task_{task_id:03d}"],
                    priority="high",
                    status="pending"
                )
            ])
            task_id += 2
            
        elif project_type == "cli":
            tasks.append(Task(
                id=f"task_{task_id:03d}",
                title="CLI 主程序",
                description="创建命令行工具主程序",
                target_path=f"{project_name}/main.py",
                verification="验收标准：main.py文件存在且包含命令行参数处理",
                dependencies=[f"task_{task_id-1:03d}"],
                priority="high",
                status="pending"
            ))
            task_id += 1
        
        # 通用任务
        tasks.extend([
            Task(
                id=f"task_{task_id:03d}",
                title="配置文件",
                description="创建项目配置文件",
                target_path=f"{project_name}/config/settings.py",
                verification="验收标准：配置文件存在且包含基本配置项",
                dependencies=[f"task_{task_id-1:03d}"],
                priority="medium",
                status="pending"
            ),
            Task(
                id=f"task_{task_id+1:03d}",
                title="依赖管理",
                description="创建依赖配置文件",
                target_path=f"{project_name}/requirements.txt",
                verification="验收标准：requirements.txt文件存在且包含必要依赖",
                dependencies=[f"task_{task_id:03d}"],
                priority="medium",
                status="pending"
            ),
            Task(
                id=f"task_{task_id+2:03d}",
                title="测试文件",
                description="创建基础测试文件",
                target_path=f"{project_name}/tests/test_main.py",
                verification="验收标准：测试文件存在且包含基本测试用例",
                dependencies=[f"task_{task_id-1:03d}"],
                priority="low",
                status="pending"
            )
        ])
        
        return tasks
    
    def create_project_structure(self, project_spec: ProjectSpec) -> None:
        """创建项目目录结构"""
        project_root = Path("output") / project_spec.project_name
        
        # 确保输出基础目录存在
        self.output_base.mkdir(exist_ok=True)
        
        # 创建项目根目录
        project_root.mkdir(parents=True, exist_ok=True)
        
        print(f"[OK] 创建项目目录: {project_root}")
        
        # 根据任务的 target_path 创建对应的目录结构
        for task in project_spec.tasks:
            target_file = Path(task.target_path)
            if not target_file.is_absolute():
                target_file = project_root / target_file
            
            target_dir = target_file.parent
            
            # 创建必要的目录
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"[OK] 创建目录: {target_dir}")
    
    def generate_spec_md(self, project_spec: ProjectSpec) -> None:
        """生成 SPEC.md 文件"""
        project_root = Path("output") / project_spec.project_name
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
        
        spec_content += f"""---
*此文档由 Vibe Coding 架构师 Agent 自动生成*
"""
        
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"[OK] 生成项目规格文档: {spec_file}")
    
    def create_code_stubs(self, project_spec: ProjectSpec) -> List[Path]:
        """根据任务创建代码占位文件"""
        project_root = Path("output") / project_spec.project_name
        created_files = []
        
        for task in project_spec.tasks:
            target_file = Path(task.target_path)
            if not target_file.is_absolute():
                target_file = project_root / target_file
            
            # 如果文件不存在，创建占位文件
            if not target_file.exists():
                # 确保目录存在
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 根据文件扩展名生成占位内容
                stub_content = self._generate_stub_content(task)
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(stub_content)
                
                created_files.append(target_file)
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
        
        return created_files
    
    def _generate_stub_content(self, task: Task) -> str:
        """根据任务类型生成占位代码内容"""
        target_file = Path(task.target_path)
        ext = target_file.suffix.lower()
        
        # 通用头部注释
        header = f'''"""
{task.title}

任务ID: {task.id}
描述: {task.description}
验收标准: {task.verification}
创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

'''
        
        # 根据文件扩展名生成不同的占位内容
        if ext == '.py':
            return header + '''def main():
    """主函数 - 待实现"""
    pass

if __name__ == "__main__":
    main()
'''
        elif ext in ['.js', '.ts']:
            return header.replace('"""', '/**') + '''/**
 * 主函数 - 待实现
 */
function main() {
    // TODO: 实现具体逻辑
}

// 执行主函数
main();
'''
        elif ext == '.md':
            return f"""# {task.title}

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
        elif ext == '.json':
            return json.dumps({
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "status": "placeholder",
                "created_at": datetime.now().isoformat(),
                "note": "这是一个占位文件，请根据实际需求实现具体内容"
            }, indent=2, ensure_ascii=False)
        else:
            return header + f"""// {task.title}
// 文件类型: {ext}
// 描述: {task.description}
// 验收标准: {task.verification}

// TODO: 请根据项目需求实现具体内容
"""
    
    def run(self, requirement: str) -> ProjectSpec:
        """运行完整的架构师流程"""
        print("[START] Vibe Coding 架构师 Agent 启动")
        print(f"[INFO] 用户需求: {requirement}")
        
        # 1. 解析用户需求
        print("\n[PROCESS] 正在分析需求...")
        project_spec = self.parse_user_requirement(requirement)
        
        # 2. 创建项目结构
        print("\n[CREATE] 正在创建项目结构...")
        self.create_project_structure(project_spec)
        
        # 3. 生成规格文档
        print("\n[GENERATE] 正在生成项目规格...")
        self.generate_spec_md(project_spec)
        
        # 4. 创建代码占位文件
        print("\n[STUB] 正在创建代码占位文件...")
        created_files = self.create_code_stubs(project_spec)
        
        project_root = Path("output") / project_spec.project_name
        
        print(f"\n[SUCCESS] 项目架构完成!")
        print(f"[PATH] 项目路径: {project_root}")
        print(f"[TASKS] 任务数量: {len(project_spec.tasks)}")
        print(f"[FILES] 创建文件数: {len(created_files) + 2}")  # +2 for SPEC.md and tasks.json
        
        return project_spec


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vibe Coding 架构师 Agent")
    parser.add_argument("requirement", nargs="?", help="项目需求描述")
    parser.add_argument("--file", "-f", help="从文件读取需求")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式输入需求（默认模式）")
    
    args = parser.parse_args()
    
    # 获取需求
    requirement = ""
    # 默认进入交互式模式
    if args.interactive or (not args.file and not args.requirement):
        # 使用交互式收集器
        try:
            collector = InteractiveCollector()
            requirement = collector.collect()
        except KeyboardInterrupt:
            print("\n[CANCEL] 用户取消操作。")
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] 交互式收集失败: {e}")
            sys.exit(1)
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                requirement = f.read().strip()
        except FileNotFoundError:
            print(f"错误: 文件不存在 {args.file}")
            return
    elif args.requirement:
        requirement = args.requirement
    else:
        print("请提供需求描述，或使用 --interactive 交互式输入")
        parser.print_help()
        return
    
    if not requirement:
        print("错误: 需求不能为空")
        return
    
    try:
        architect = VibeArchitect()
        project_spec = architect.run(requirement)
        print(f"\n[COMPLETE] 项目 '{project_spec.project_name}' 架构设计完成!")
    except Exception as e:
        print(f"[ERROR] 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()