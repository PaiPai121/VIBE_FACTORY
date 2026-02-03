import os
import json
from pathlib import Path
from typing import Dict, Any, List
from schema.project import ProjectSpec
from pydantic import ValidationError


class Architect:
    """
    架构师类，负责根据JSON规格说明物理落地文件和目录
    遵循目录隔离原则，业务代码必须存在于 output/项目名/src 目录下
    """
    
    def __init__(self, base_output_dir: str = "output"):
        self.base_output_dir = Path(base_output_dir)
        
    def create_project_structure(self, project_spec: Dict[str, Any]) -> bool:
        """
        根据项目规格创建项目结构
        遵循目录隔离原则，确保业务代码存在于指定目录
        """
        try:
            # 验证项目规格
            spec = ProjectSpec(**project_spec)
        except ValidationError as e:
            print(f"项目规格验证失败: {e}")
            return False

        # 创建项目根目录
        project_root = self.base_output_dir / spec.project_name
        project_root.mkdir(parents=True, exist_ok=True)

        # 创建标准目录结构
        dirs_to_create = [
            project_root / "src",
            project_root / "tests",
            project_root / "docs",
            project_root / "config",
            project_root / "scripts"
        ]

        for dir_path in dirs_to_create:
            dir_path.mkdir(exist_ok=True)

        # 创建 README.md
        readme_path = project_root / "README.md"
        readme_content = f"# {spec.project_name}\n\n{spec.description}\n\n## 项目结构\n\n此项目由 Vibe Nexus 框架自动生成。\n"
        readme_path.write_text(readme_content, encoding='utf-8')

        # 创建架构提案文档 (TECH_PROPOSAL.md)
        tech_proposal_path = project_root / "TECH_PROPOSAL.md"
        tech_proposal_content = f"# {spec.project_name} - 技术方案白皮书\n\n{spec.architecture_proposal}\n\n## 项目任务技术要求\n\n"
        for task in spec.tasks:
            tech_proposal_content += f"\n### 任务: {task.title}\n"
            tech_proposal_content += f"**技术要求**: {task.technical_requirement}\n"
            tech_proposal_content += f"**目标路径**: {task.target_path}\n"
            tech_proposal_content += f"**验证标准**: {task.verification}\n"
            tech_proposal_content += f"**灵活性**: {task.flexibility}\n"
        tech_proposal_path.write_text(tech_proposal_content, encoding='utf-8')

        # 创建开发日志 (DEVELOPMENT_LOG.md)
        dev_log_path = project_root / "DEVELOPMENT_LOG.md"
        dev_log_content = f"# {spec.project_name} - 开发日志\n\n## 设计意图留言板\n\n此文件记录了所有任务的初始设计意图，供下游Agent参考。\n\n"
        for task in spec.tasks:
            dev_log_content += f"\n### 任务: {task.title}\n"
            dev_log_content += f"- **描述**: {task.description}\n"
            dev_log_content += f"- **目标路径**: {task.target_path}\n"
            dev_log_content += f"- **灵活性**: {task.flexibility}\n"
            dev_log_content += f"- **技术要求**: {task.technical_requirement}\n"
            dev_log_content += f"- **验证标准**: {task.verification}\n\n"
        dev_log_path.write_text(dev_log_content, encoding='utf-8')

        # 创建项目配置文件
        config_path = project_root / "config" / "project.json"
        config_content = {
            "project_name": spec.project_name,
            "description": spec.description,
            "version": spec.version,  # 确保包含版本号以实现高度确定性
            "architecture_proposal": spec.architecture_proposal,
            "created_at": spec.created_at or "",
            "updated_at": spec.updated_at or ""
        }
        config_path.write_text(json.dumps(config_content, ensure_ascii=False, indent=2), encoding='utf-8')

        # 根据任务列表创建文件和目录
        for task in spec.tasks:
            success = self._create_task_artifacts(task, project_root)
            if not success:
                print(f"创建任务 {task.id} 的产物失败: {task.title}")
                return False

        print(f"项目 {spec.project_name} 结构创建成功！")
        return True
    
    def _create_task_artifacts(self, task: 'Task', project_root: Path) -> bool:
        """
        根据任务创建对应的文件和目录
        遵循PnC准则，每个任务都有物理路径和验证步骤
        """
        try:
            # 解析目标路径
            target_path = project_root / task.target_path.lstrip('/')

            # 如果目标路径以 / 结尾，表示是目录
            if task.target_path.endswith('/'):
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                # 否则是文件，创建父目录并写入内容
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # 根据文件扩展名生成默认内容
                if target_path.suffix.lower() in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                    content = self._generate_default_code_content(task, target_path.suffix)
                elif target_path.suffix.lower() == '.md':
                    content = self._generate_default_markdown_content(task)
                elif target_path.suffix.lower() in ['.json', '.yaml', '.yml']:
                    content = self._generate_default_config_content(task)
                else:
                    content = self._generate_default_generic_content(task)

                target_path.write_text(content, encoding='utf-8')

            # 创建验证脚本（如果适用）
            self._create_verification_script(task, project_root)

            # 为src目录下的任务强制创建测试占位
            if task.target_path.startswith('src/') and task.target_path.endswith(('.py', '.js', '.ts')):
                self._create_test_placeholder(task, project_root)

            return True
        except Exception as e:
            print(f"创建任务产物失败 {task.id} ({task.title}): {str(e)}")
            return False

    def _create_test_placeholder(self, task: 'Task', project_root: Path):
        """
        为src目录下的任务强制创建测试占位
        """
        # 生成测试文件名
        src_path = task.target_path
        if src_path.startswith('src/'):
            relative_path = src_path[4:]  # 移除 'src/' 前缀
        else:
            relative_path = src_path

        # 生成测试文件路径
        test_dir = project_root / "tests"
        if relative_path.endswith('.py'):
            test_file_name = f"test_{relative_path.replace('/', '.').replace('.', '_')}.py"
        elif relative_path.endswith(('.js', '.ts')):
            test_file_name = f"test_{relative_path.replace('/', '.').replace('.', '_')}.js"
        else:
            test_file_name = f"test_{relative_path.replace('/', '.').replace('.', '_')}.py"

        test_file_path = test_dir / test_file_name

        # 确保测试目录存在
        test_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 生成测试内容，将verification内容填入Docstring
        if relative_path.endswith('.py'):
            test_content = f'''"""
Test for {task.title}

Task Description: {task.description}
Verification Criteria: {task.verification}
Technical Requirement: {task.technical_requirement}
Flexibility: {task.flexibility}
"""
import unittest


class Test{task.title.replace(" ", "").replace("-", "")}(unittest.TestCase):
    """Test class for {task.title}"""

    def test_implementation(self):
        """Test that {task.title} meets verification criteria: {task.verification}"""
        # TODO: Implement test based on verification criteria
        # Task: {task.description}
        # Technical Requirement: {task.technical_requirement}
        # Flexibility: {task.flexibility}
        self.assertTrue(True)  # Replace with actual test


if __name__ == "__main__":
    unittest.main()
'''
        else:  # For JS/TS or other files
            test_content = f'''/**
 * Test for {task.title}
 *
 * Task Description: {task.description}
 * Verification Criteria: {task.verification}
 * Technical Requirement: {task.technical_requirement}
 * Flexibility: {task.flexibility}
 */

// TODO: Implement test based on verification criteria
// Task: {task.description}
// Technical Requirement: {task.technical_requirement}
// Flexibility: {task.flexibility}

console.log("Test placeholder for {task.title}");
'''

        test_file_path.write_text(test_content, encoding='utf-8')
    
    def _generate_default_code_content(self, task: 'Task', extension: str) -> str:
        """
        为代码文件生成默认内容
        """
        if extension == '.py':
            return f'''"""
{task.title}

Description: {task.description}
"""
def main():
    # TODO: 实现 {task.title}
    # {task.description}
    pass

if __name__ == "__main__":
    main()
'''
        elif extension in ['.js', '.ts', '.jsx', '.tsx']:
            return f'''/**
 * {task.title}
 * 
 * Description: {task.description}
 */

// TODO: 实现 {task.title}
// {task.description}

export const {task.title.replace(" ", "").replace("-", "_")} = () => {{
    // Implementation goes here
}};
'''
        else:
            return f"# {task.title}\n# Description: {task.description}\n\n"
    
    def _generate_default_markdown_content(self, task: 'Task') -> str:
        """
        为Markdown文件生成默认内容
        """
        return f"""# {task.title}

## 描述
{task.description}

## 实现细节
TODO: 添加实现细节

## 验证步骤
{task.verification}
"""
    
    def _generate_default_config_content(self, task: 'Task') -> str:
        """
        为配置文件生成默认内容
        """
        return json.dumps({"task_id": task.id, "title": task.title, "description": task.description}, 
                         ensure_ascii=False, indent=2)
    
    def _generate_default_generic_content(self, task: 'Task') -> str:
        """
        为通用文件生成默认内容
        """
        return f"{task.title}\n\n{task.description}\n\nVerification: {task.verification}\n"
    
    def _create_verification_script(self, task: 'Task', project_root: Path):
        """
        为任务创建验证脚本
        """
        # 创建测试文件用于验证
        if task.target_path.endswith(('.py', '.js', '.ts')):
            test_dir = project_root / "tests"
            test_dir.mkdir(exist_ok=True)
            
            # 生成测试文件名
            test_file_name = f"test_{task.target_path.split('/')[-1].replace('.', '_').replace('-', '_')}"
            test_file_path = test_dir / f"{test_file_name}.py"
            
            test_content = f'''"""
测试 {task.title}
验证步骤: {task.verification}
"""
import unittest


class Test{task.title.replace(" ", "").replace("-", "")}(unittest.TestCase):
    def test_implementation(self):
        """验证 {task.title} 是否按预期工作"""
        # TODO: 根据验证步骤 {task.verification} 编写测试
        self.assertTrue(True)  # 替换为实际测试


if __name__ == "__main__":
    unittest.main()
'''
            test_file_path.write_text(test_content, encoding='utf-8')