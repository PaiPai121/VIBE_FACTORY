#!/usr/bin/env python3
"""
Vibe Coding 架构师 Agent - 主程序
自动化项目架构设计、目录创建和代码占位生成
使用 Google Gemini API 进行智能分析
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import google.generativeai as genai
    from pydantic import BaseModel
except ImportError as e:
    print(f"请安装必要的依赖: pip install -r requirements.txt")
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
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        """初始化架构师"""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("需要设置 GOOGLE_API_KEY 环境变量或提供 api_key 参数")
        
        # 配置 Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.output_base = Path("output")
        
    def load_system_prompt(self) -> str:
        """加载系统提示"""
        system_file = Path("prompts/system.txt")
        if not system_file.exists():
            raise FileNotFoundError(f"系统提示文件不存在: {system_file}")
        
        with open(system_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def load_architect_prompt(self) -> str:
        """加载架构师提示"""
        architect_file = Path("prompts/architect.txt")
        if not architect_file.exists():
            raise FileNotFoundError(f"架构师提示文件不存在: {architect_file}")
        
        with open(architect_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def parse_user_requirement(self, requirement: str) -> ProjectSpec:
        """解析用户需求并生成项目规格"""
        system_prompt = self.load_system_prompt()
        architect_prompt = self.load_architect_prompt()
        
        # 构建完整提示
        full_prompt = f"{architect_prompt}\n\n用户需求:\n{requirement}\n\n请根据上述格式输出 JSON 格式的项目规格。严格按照JSON格式返回，不要包含任何其他文本。"
        
        try:
            # 使用 Gemini API 生成项目规格
            response = self.model.generate_content(full_prompt)
            
            if not response.text:
                raise ValueError("Gemini API 返回空响应")
            
            # 提取 JSON 内容
            json_text = self._extract_json_from_response(response.text)
            
            # 解析 JSON 并创建 ProjectSpec
            try:
                project_data = json.loads(json_text)
                return self._create_project_spec_from_data(project_data)
            except json.JSONDecodeError as e:
                print(f"JSON 解析失败: {e}")
                print(f"原始响应: {response.text}")
                raise
            
        except Exception as e:
            print(f"Gemini API 调用失败: {e}")
            # 降级方案：手动创建基本规格
            return self._create_fallback_spec(requirement)
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """从响应中提取 JSON 内容"""
        # 寻找 JSON 块
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        
        # 寻找 { ... } 块
        if "{" in response_text and "}" in response_text:
            start = response_text.find("{")
            # 寻找最后一个 }
            end = response_text.rfind("}") + 1
            return response_text[start:end].strip()
        
        # 如果都没有，直接返回原文本
        return response_text.strip()
    
    def _create_project_spec_from_data(self, data: Dict[str, Any]) -> ProjectSpec:
        """从数据字典创建 ProjectSpec 对象"""
        # 提取任务数据
        tasks_data = data.get("tasks", [])
        tasks = []
        
        for task_data in tasks_data:
            task = Task(
                id=task_data.get("id", ""),
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                target_path=task_data.get("target_path", ""),
                verification=task_data.get("verification", ""),
                dependencies=task_data.get("dependencies", []),
                priority=task_data.get("priority", "medium"),
                status=task_data.get("status", "pending")
            )
            tasks.append(task)
        
        # 创建 ProjectSpec 对象（使用简化版本）
        return ProjectSpec(
            project_name=data.get("project_name", data.get("name", "未命名项目")),
            description=data.get("description", "项目描述"),
            tasks=tasks
        )
    
    def _create_fallback_spec(self, requirement: str) -> ProjectSpec:
        """创建备用项目规格（当 API 调用失败时）"""
        project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        fallback_task = Task(
            id="task_001",
            title="基础项目设置",
            description="根据用户需求创建基础项目结构",
            target_path=f"output/{project_name}/README.md",
            verification="验收标准：README.md 文件存在且包含项目描述",
            priority="high",
            status="pending"
        )
        
        return ProjectSpec(
            project_name=project_name,
            description=f"基于需求的项目: {requirement[:100]}...",
            tasks=[fallback_task]
        )
    
    def create_project_structure(self, project_spec: ProjectSpec) -> None:
        """创建项目目录结构"""
        project_root = Path(project_spec.project_name) if hasattr(project_spec, 'project_name') else Path("output", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # 确保输出基础目录存在
        self.output_base.mkdir(exist_ok=True)
        
        # 创建项目根目录
        project_root.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ 创建项目目录: {project_root}")
        
        # 根据任务的 target_path 创建对应的目录结构
        for task in project_spec.tasks:
            target_file = Path(task.target_path)
            target_dir = target_file.parent
            
            # 创建必要的目录
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {target_dir}")
    
    def generate_spec_md(self, project_spec: ProjectSpec) -> None:
        """生成 SPEC.md 文件"""
        project_root = Path(project_spec.project_name) if hasattr(project_spec, 'project_name') else Path("output", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        spec_file = project_root / "SPEC.md"
        
        project_name = project_spec.project_name if hasattr(project_spec, 'project_name') else "未命名项目"
        project_desc = project_spec.description
        
        spec_content = f"""# {project_name} 项目规格

## 基本信息
- **项目名称**: {project_name}
- **描述**: {project_desc}
- **创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
        
        print(f"✓ 生成项目规格文档: {spec_file}")
    
    def create_code_stubs(self, project_spec: ProjectSpec) -> List[Path]:
        """根据任务创建代码占位文件"""
        project_root = Path(project_spec.project_name) if hasattr(project_spec, 'project_name') else Path("output", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        created_files = []
        
        for task in project_spec.tasks:
            target_file = project_root / task.target_path if not Path(task.target_path).is_absolute() else Path(task.target_path)
            
            # 如果文件不存在，创建占位文件
            if not target_file.exists():
                # 确保目录存在
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 根据文件扩展名生成占位内容
                stub_content = self._generate_stub_content(task)
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(stub_content)
                
                created_files.append(target_file)
                print(f"✓ 创建代码占位文件: {target_file}")
        
        # 生成任务JSON文件
        tasks_file = project_root / "tasks.json"
        tasks_data = {
            "generated_at": datetime.now().isoformat(),
            "tasks": [task.model_dump() for task in project_spec.tasks]
        }
        
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 生成任务配置文件: {tasks_file}")
        
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
        print("🚀 Vibe Coding 架构师 Agent 启动")
        print(f"📋 用户需求: {requirement}")
        
        # 1. 解析用户需求
        print("\n🔍 正在使用 Gemini AI 分析需求...")
        project_spec = self.parse_user_requirement(requirement)
        
        # 2. 创建项目结构
        print("\n🏗️ 正在创建项目结构...")
        self.create_project_structure(project_spec)
        
        # 3. 生成规格文档
        print("\n📄 正在生成项目规格...")
        self.generate_spec_md(project_spec)
        
        # 4. 创建代码占位文件
        print("\n📝 正在创建代码占位文件...")
        created_files = self.create_code_stubs(project_spec)
        
        project_root = Path(project_spec.project_name) if hasattr(project_spec, 'project_name') else Path("output", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        print(f"\n✅ 项目架构完成!")
        print(f"📁 项目路径: {project_root}")
        print(f"📊 任务数量: {len(project_spec.tasks)}")
        print(f"📝 创建文件数: {len(created_files) + 2}")  # +2 for SPEC.md and tasks.json
        
        return project_spec


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vibe Coding 架构师 Agent")
    parser.add_argument("requirement", nargs="?", help="项目需求描述")
    parser.add_argument("--file", "-f", help="从文件读取需求")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式输入需求")
    parser.add_argument("--model", "-m", default="gemini-1.5-flash", help="Gemini 模型名称")
    
    args = parser.parse_args()
    
    # 获取需求
    requirement = ""
    if args.interactive:
        # 使用交互式收集器
        try:
            collector = InteractiveCollector()
            requirement = collector.collect()
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作。")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 交互式收集失败: {e}")
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
        architect = VibeArchitect(model_name=args.model)
        project_spec = architect.run(requirement)
        project_name = project_spec.project_name if hasattr(project_spec, 'project_name') else "未命名项目"
        print(f"\n🎉 项目 '{project_name}' 架构设计完成!")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()