import os
import json
import subprocess
import sys
import re
import functools
from pathlib import Path
from typing import Dict, Any, List
from schema.project import ProjectSpec, Task
from providers.base import BaseProvider


def exception_handler(func):
    """
    异常捕获装饰器，用于自动捕获和处理运行时异常
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"函数 {func.__name__} 执行出错: {str(e)}")
            raise e
    return wrapper


class EnvironmentManager:
    """
    环境管理器，负责依赖检测和安装
    """

    @staticmethod
    def detect_missing_modules(error_msg: str, project_root_path: Path = None, project_tasks: List = None) -> List[str]:
        """
        从错误消息中检测缺失的模块
        """
        # 查找 ModuleNotFoundError 或 ImportError 中的模块名
        patterns = [
            r"ModuleNotFoundError: No module named '([^']+)'",
            r"ImportError: No module named '([^']+)'",
            r"No module named ([^,\s]+)",  # 更通用的匹配模式
            r"cannot import name '([^']+)' from",  # 处理 from import 错误
            r"name '([^']+)' is not defined"  # 处理名称未定义错误（可能需要安装包）
        ]
        
        modules = []
        for pattern in patterns:
            matches = re.findall(pattern, error_msg)
            for match in matches:
                # 确保匹配到的是模块名而不是其他文本
                if isinstance(match, tuple):
                    module = next((m for m in match if m), None)
                else:
                    module = match
                if module and module not in modules:
                    # 过滤掉一些常见的非模块名匹配
                    if not any(skip in module for skip in ['built-in', 'file', '<frozen', '__main__']):
                        # 检查是否是本地模块路径
                        if project_root_path:
                            # 分割模块名，检查第一部分是否是项目中的目录
                            module_parts = module.split('.')
                            first_part = module_parts[0]
                            
                            # 检查项目中是否存在对应的目录
                            possible_paths = [
                                project_root_path / f"{first_part}",
                                project_root_path / "src" / f"{first_part}",
                                project_root_path / "lib" / f"{first_part}",
                            ]
                            
                            is_local_module = any(path.exists() and path.is_dir() for path in possible_paths)
                            
                            if is_local_module:
                                # 这是本地模块，不需要安装
                                continue
                        
                        # 检查是否是项目中的任务模块（即待生成的文件），如果是则不安装
                        if project_tasks:
                            task_target_modules = []
                            for task in project_tasks:
                                target_path = task.target_path
                                # 提取模块名，例如 src/image_processing/puzzle_recognition.py -> image_processing.puzzle_recognition
                                if target_path.endswith('.py'):
                                    parts = target_path.replace('/', '.').replace('\\', '.').split('.')
                                    if len(parts) > 1:
                                        module_name = '.'.join(parts[:-1])  # 去掉.py后缀
                                        task_target_modules.append(module_name)
                            
                            # 如果模块名在任务列表中，则不视为需要安装的包
                            if module in task_target_modules:
                                print(f"检测到项目任务模块缺失: {module} (这是一个待生成的文件，不是外部包)")
                                continue
                        
                        # 映射常见模块名到正确的包名
                        if module == 'cv2':
                            modules.append('opencv-python')
                        elif module == 'PIL':
                            modules.append('Pillow')
                        elif module == 'sklearn':
                            modules.append('scikit-learn')
                        elif module == 'flask':
                            modules.append('Flask')
                        elif module == 'jwt':
                            modules.append('PyJWT')
                        elif module == 'cv2':
                            modules.append('opencv-python')
                        else:
                            modules.append(module)

        return modules

    @staticmethod
    def install_missing_modules(modules: List[str], project_root_path: Path = None) -> bool:
        """
        安装缺失的模块到虚拟环境中
        """
        success = True
        for module in modules:
            print(f"正在静默安装缺失的模块: {module}")
            try:
                # 检查是否存在虚拟环境
                if project_root_path:
                    venv_path = project_root_path / "venv"

                    # 确保虚拟环境存在
                    if not venv_path.exists():
                        print(f"虚拟环境不存在，正在创建: {venv_path}")
                        import venv
                        venv.create(venv_path, with_pip=True)

                    # 使用虚拟环境安装
                    if os.name == 'nt':  # Windows
                        pip_path = venv_path / "Scripts" / "pip.exe"
                    else:  # Unix/Linux/macOS
                        pip_path = venv_path / "bin" / "pip"

                    result = subprocess.run(
                        [str(pip_path), "install", module],
                        capture_output=True,
                        text=True
                    )
                else:
                    # 如果没有提供项目路径，使用全局pip
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", module],
                        capture_output=True,
                        text=True
                    )

                if result.returncode == 0:
                    print(f"成功安装模块: {module}")
                else:
                    print(f"安装模块 {module} 失败: {result.stderr}")
                    success = False
            except Exception as e:
                print(f"安装模块 {module} 时发生异常: {str(e)}")
                success = False
        return success


class Coder:
    """
    施工员类，负责根据项目规格和任务依赖关系，
    调用AI将代码填充到Architect生成的占位文件中
    """

    def __init__(self, project_root_path: str, ai_provider: BaseProvider):
        """
        初始化Coder
        :param project_root_path: 项目根路径
        :param ai_provider: AI提供者实例
        """
        self.project_root_path = Path(project_root_path)
        self.ai_provider = ai_provider
        self.project_spec = self._load_project_spec()
        self.env_manager = EnvironmentManager()

        # 为项目设置虚拟环境
        self.setup_project_environment()

    def setup_project_environment(self):
        """
        为项目设置虚拟环境
        """
        import venv
        venv_path = self.project_root_path / "venv"

        if not venv_path.exists():
            print(f"正在为项目创建虚拟环境: {venv_path}")
            venv.create(venv_path, with_pip=True)
            print("虚拟环境创建成功")
        else:
            print("虚拟环境已存在")

        # 安装项目依赖
        requirements_path = self.project_root_path / "requirements.txt"
        if requirements_path.exists():
            self._install_project_requirements(requirements_path)

    def _install_project_requirements(self, requirements_path):
        """
        安装项目依赖到虚拟环境中
        """
        venv_path = self.project_root_path / "venv"
        if venv_path.exists():
            if os.name == 'nt':  # Windows
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:  # Unix/Linux/macOS
                pip_path = venv_path / "bin" / "pip"

            print(f"正在虚拟环境中安装项目依赖: {requirements_path}")
            try:
                result = subprocess.run(
                    [str(pip_path), "install", "-r", str(requirements_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("项目依赖安装成功")
                else:
                    print(f"项目依赖安装失败: {result.stderr}")
            except Exception as e:
                print(f"项目依赖安装时发生异常: {str(e)}")
        else:
            print("虚拟环境不存在，无法安装项目依赖")

    def _load_project_spec(self) -> ProjectSpec:
        """
        加载项目配置文件
        """
        config_path = self.project_root_path / "config" / "project.json"
        if not config_path.exists():
            raise FileNotFoundError(f"项目配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # 直接使用config/project.json中的任务信息
        # 不再尝试从其他文件中合并任务
        full_spec_data = config_data.copy()
        
        # 确保任务信息存在
        if 'tasks' not in full_spec_data or not full_spec_data['tasks']:
            raise ValueError("项目配置文件中未包含任务信息")

        return ProjectSpec(**full_spec_data)

    def _parse_tasks_from_dev_log(self, dev_log_path: Path) -> List[Task]:
        """
        从DEVELOPMENT_LOG.md解析任务信息
        """
        with open(dev_log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单解析DEVELOPMENT_LOG.md中的任务信息
        import re

        # 查找任务部分
        task_pattern = r'### 任务: (.*?)\n- \*\*描述\*\*: (.*?)\n- \*\*目标路径\*\*: (.*?)\n- \*\*灵活性\*\*: (.*?)\n- \*\*技术要求\*\*: (.*?)\n- \*\*验证标准\*\*: (.*?)\n'
        matches = re.findall(task_pattern, content, re.DOTALL)

        tasks = []
        for i, match in enumerate(matches):
            title, description, target_path, flexibility, technical_requirement, verification = match

            # 提取ID（如果有）
            id_match = re.search(r'任务 (\d+):', content[content.find(match[0])-50:content.find(match[0])+len(match[0])+50])
            task_id = int(id_match.group(1)) if id_match else i + 1

            # 处理灵活性值，将其转换为正确的格式
            flexibility_value = flexibility.strip()
            if 'FIXED' in flexibility_value:
                flexibility_value = 'fixed'
            elif 'FLEXIBLE' in flexibility_value:
                flexibility_value = 'flexible'

            task = Task(
                id=task_id,
                title=title.strip(),
                description=description.strip(),
                target_path=target_path.strip(),
                verification=verification.strip(),
                flexibility=flexibility_value,
                technical_requirement=technical_requirement.strip(),
                dependencies=[]  # 从日志中难以提取依赖关系，暂时设为空
            )
            tasks.append(task)

        return tasks

    def _topological_sort(self, tasks: List[Task]) -> List[Task]:
        """
        根据任务依赖关系进行拓扑排序
        确保依赖项（如接口/基类）先执行
        """
        # 构建邻接表和入度表
        graph = {task.id: [] for task in tasks}
        in_degree = {task.id: 0 for task in tasks}

        # 填充图和入度表
        for task in tasks:
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id in graph:
                        graph[dep_id].append(task.id)
                        in_degree[task.id] += 1

        # 拓扑排序 - Kahn算法
        queue = []
        for task_id, degree in in_degree.items():
            if degree == 0:
                # 找到对应的Task对象
                for task in tasks:
                    if task.id == task_id:
                        queue.append(task)
                        break

        sorted_tasks = []
        while queue:
            current_task = queue.pop(0)
            sorted_tasks.append(current_task)

            # 更新相邻节点的入度
            for neighbor_id in graph[current_task.id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    # 找到对应的Task对象
                    for task in tasks:
                        if task.id == neighbor_id:
                            queue.append(task)
                            break

        # 检查是否存在环
        if len(sorted_tasks) != len(tasks):
            raise ValueError("任务依赖关系中存在循环依赖")

        return sorted_tasks

    async def execute_coding_tasks(self):
        """
        执行编码任务的主要方法
        """
        # 按依赖关系对任务进行排序
        sorted_tasks = self._topological_sort(self.project_spec.tasks)

        # 遍历排序后的任务，逐个生成代码
        for task in sorted_tasks:
            await self._execute_single_task(task)

        # 主动发现未完成的任务
        await self._discover_and_complete_pending_tasks()

    async def _discover_and_complete_pending_tasks(self):
        """
        主动发现并完成遗漏的任务
        """
        print("🔍 开始主动发现遗漏任务...")

        # 遍历 src/ 目录下所有文件
        src_path = self.project_root_path / "src"
        if src_path.exists():
            for file_path in src_path.glob("*.py"):
                if file_path.name != "__init__.py":
                    await self._check_and_complete_file(file_path)

        print("✅ 主动发现遗漏任务完成")

    async def _check_and_complete_file(self, file_path):
        """
        检查并完成单个文件
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含 TODO 或者描述性注释
        has_todo = "TODO" in content or "todo" in content
        has_description = "Description:" in content or "Technical Requirement:" in content or "description" in content.lower()

        if has_todo or has_description:
            print(f"发现待完成文件: {file_path.name}")

            # 检查文件内容的实质性
            if not self._has_substantial_content(content):
                print(f"  文件 {file_path.name} 内容不足，需要重新生成")

                # 创建一个虚拟任务来处理这个文件
                relative_path = str(file_path.relative_to(self.project_root_path))

                from schema.project import Task
                task = Task(
                    id=999,  # 临时ID
                    title=f"Complete {file_path.stem}",
                    description=f"Complete the implementation of {file_path.name}",
                    target_path=relative_path,
                    verification="Code should run without errors and not contain TODO comments",
                    flexibility="fixed",
                    technical_requirement="Remove all TODO comments and implement complete functionality",
                    dependencies=[]
                )

                # 执行任务
                await self._execute_single_task(task)

    def _has_substantial_content(self, content):
        """
        检查文件是否有实质性内容
        """
        lines = content.split('\n')

        # 过滤注释和空行
        code_lines = []
        in_multiline_comment = False

        for line in lines:
            stripped = line.strip()

            # 检查多行注释的开始和结束
            if '"""' in stripped or "'''" in stripped:
                in_multiline_comment = not in_multiline_comment
                continue

            # 跳过多行注释内部
            if in_multiline_comment:
                continue

            # 跳过单行注释和空行
            if stripped.startswith('#') or not stripped:
                continue

            code_lines.append(stripped)

        # 检查是否包含 TODO 或 pass
        has_todo = any("TODO" in line.upper() for line in code_lines)
        has_pass = any("pass" in line and line.strip() == "pass" for line in code_lines)

        # 检查代码行数
        code_line_count = len(code_lines)

        # 检查逻辑密度 - 计算非简单语句的数量
        substantial_lines = 0
        for line in code_lines:
            # 排除简单的赋值、导入等
            if (any(keyword in line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'with ', 'return', 'yield', 'import', 'from'])
                or len(line.strip()) > 20):  # 长度超过20的行通常包含实质内容
                substantial_lines += 1

        # 如果包含 TODO 或 pass，或者代码行数少于阈值，或者逻辑密度低，则认为内容不足
        return not has_todo and not has_pass and code_line_count >= 10 and substantial_lines >= 3

    async def _execute_single_task(self, task: Task):
        """
        执行单个任务的编码工作 - 实现"施工-验证-修复"递归闭环
        """
        print(f"开始处理任务: {task.title} (ID: {task.id})")

        # 确保项目包结构正确
        self._ensure_package_structure()

        # 读取目标文件
        target_path = self.project_root_path / task.target_path.lstrip('/')

        if not target_path.exists():
            print(f"警告: 目标文件不存在: {target_path}")
            # 创建文件
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch()

        # 初始化循环控制变量
        completed = False
        attempt_count = 0
        max_attempts = 10  # 设置最大尝试次数，防止无限循环

        while not completed and attempt_count < max_attempts:
            attempt_count += 1
            print(f"  尝试第 {attempt_count} 次生成和验证代码...")

            # 读取当前文件内容
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                with open(target_path, 'r', encoding='gbk') as f:
                    current_content = f.read()

            # 构造AI请求的Prompt，加强约束
            prompt = self._construct_enhanced_prompt(task, current_content)

            try:
                # 调用AI生成代码
                response = await self.ai_provider.generate_response(prompt)

                # 提取AI生成的代码
                generated_code = self._extract_code_from_response(response, current_content)

                # 将生成的代码写回文件
                self._write_code_to_file(target_path, generated_code, current_content)

                # 检查全局依赖
                missing_deps = self._check_global_dependencies(generated_code)
                if missing_deps:
                    print(f"  检测到缺失的全局依赖: {missing_deps}")
                    # 让AI修复缺失的依赖
                    generated_code = await self._fix_code_with_ai(target_path, f"Missing dependencies: {', '.join(missing_deps)}")
                    self._write_code_to_file(target_path, generated_code, current_content)

                # 尝试运行文件以验证代码是否正确
                success, error_msg = self._test_run_file(target_path)

                if success:
                    # 检查实质性内容
                    with open(target_path, 'r', encoding='utf-8') as f:
                        final_content = f.read()

                    if self._has_substantial_content(final_content):
                        # 代码运行成功且内容充实，任务完成
                        print(f"  任务 {task.title} 代码生成并验证成功!")
                        completed = True
                    else:
                        print(f"  任务 {task.title} 代码内容不足，继续生成...")
                        continue
                else:
                    # 代码运行失败，分析错误并尝试修复
                    print(f"  代码运行失败: {error_msg}")

                    # 检查是否是模块缺失错误
                    if "ModuleNotFoundError" in error_msg or "ImportError" in error_msg:
                        missing_modules = self.env_manager.detect_missing_modules(error_msg, self.project_root_path, self.project_spec.tasks if hasattr(self, 'project_spec') and self.project_spec else None)
                        if missing_modules:
                            print(f"  检测到缺失的模块: {missing_modules}")
                            install_success = self.env_manager.install_missing_modules(missing_modules, self.project_root_path)

                            if install_success:
                                # 重新尝试运行
                                success, error_msg = self._test_run_file(target_path)
                                if success:
                                    # 再次检查实质性内容
                                    with open(target_path, 'r', encoding='utf-8') as f:
                                        final_content = f.read()

                                    if self._has_substantial_content(final_content):
                                        print(f"  依赖安装成功，代码验证通过!")
                                        completed = True
                                    else:
                                        print(f"  依赖安装成功但内容不足，继续生成...")
                                    continue

                    # 如果不是依赖问题或依赖安装后仍失败，让AI修复代码
                    print(f"  让AI修复代码...")
                    generated_code = await self._fix_code_with_ai(target_path, error_msg)
                    self._write_code_to_file(target_path, generated_code, current_content)

                    # 再次验证修复后的代码
                    success, error_msg = self._test_run_file(target_path)
                    if success:
                        # 检查修复后的实质性内容
                        with open(target_path, 'r', encoding='utf-8') as f:
                            final_content = f.read()

                        if self._has_substantial_content(final_content):
                            print(f"  代码修复成功，验证通过!")
                            completed = True
                        else:
                            print(f"  代码修复成功但内容不足，继续生成...")

            except Exception as e:
                print(f"  AI生成代码失败: {str(e)}")
                # 如果AI生成失败，尝试重新生成
                if attempt_count >= max_attempts:
                    raise RuntimeError(f"AI生成代码失败，任务 {task.id} ({task.title}): {str(e)}") from e

        if not completed:
            raise RuntimeError(f"经过 {max_attempts} 次尝试后，任务 {task.id} ({task.title}) 仍未成功完成")

        # 更新开发日志
        self._update_development_log(task)

        print(f"任务完成: {task.title} (ID: {task.id})")

    def _construct_enhanced_prompt(self, task: Task, current_content: str) -> str:
        """
        构造增强的Prompt，包含强制约束
        """
        # 检查是否是UI任务
        is_ui_task = "GUI" in task.title or "gui" in task.title or "UI" in task.title or "ui" in task.title or "interface" in task.description.lower()
        
        ui_specific_guidance = ""
        if is_ui_task:
            ui_specific_guidance = """
## UI 任务专项指导
- 必须实现真实的 PyQt5 界面类（如 QMainWindow, QWidget 等）
- 必须包含具体的界面布局代码（QVBoxLayout, QHBoxLayout 等）
- 必须实现真实的交互组件（QPushButton, QLabel, QFileDialog 等）
- 必须包含信号槽连接逻辑
- 严禁生成空壳代码或仅包含注释的代码
- 必须实现完整的界面功能，包括图像显示、按钮响应等
"""
        
        prompt = f"""
你是一个专业的软件工程师，正在实现一个项目的一部分。

## 项目全局方案
{self.project_spec.architecture_proposal}

## 任务信息
- 任务标题: {task.title}
- 任务描述: {task.description}
- 技术要求: {task.technical_requirement}
- 目标路径: {task.target_path}
- 验收标准: {task.verification}

## 当前文件内容
```{self._get_file_extension(task.target_path)}
{current_content}
```

## 任务指令
请根据以上信息，完善或替换当前文件的内容。你需要：
1. 实现任务描述中提到的功能
2. 遵循技术要求中的约束
3. 确保代码满足验收标准
4. 保持代码风格与现有代码一致
5. 如果有依赖其他模块，请确保接口兼容

## 重要约束
- 你必须删除所有原有代码中的 TODO 注释，并代之以真实的逻辑实现
- 如果保留了 TODO，本次任务将被视为失败
- 代码必须是完整的、可运行的实现
- 代码必须包含实质性的业务逻辑，不能只是简单的print语句
- 代码行数必须超过60行（对于业务逻辑模块）
- 请只返回代码内容，不要包含额外的解释。

## 技术实现要求
- 对于GUI模块：必须实现真实的 PyQt5 信号槽机制，包含具体的界面组件和交互逻辑
- 对于图像处理模块：必须实现具体的 OpenCV 处理函数（如 cv2.findContours, cv2.matchTemplate 等），严禁使用简单的print代替逻辑
- 对于API模块：必须实现完整的路由和业务处理逻辑
- 对于安全模块：必须实现真实的认证和授权机制

## 环境关联性要求
- 如果需要调用其他模块（如 src/data_preprocessing.py, src/feature_extraction.py 等），请确保 import 语句路径正确
- 检查所有依赖模块的类名和函数名是否正确
- 确保创建必要的目录（如 data/ 目录）以避免文件路径错误

{ui_specific_guidance}
"""
        return prompt

    def _ensure_package_structure(self):
        """
        确保项目中的目录被正确识别为Python包（即包含__init__.py文件）
        """
        # 遍历项目中的所有目录
        for dir_path in self.project_root_path.rglob('*'):
            if dir_path.is_dir():
                # 检查目录是否包含.py文件，如果是，则确保它是一个包
                has_py_files = any(dir_path.glob('*.py'))
                init_file = dir_path / '__init__.py'

                if has_py_files and not init_file.exists():
                    # 创建__init__.py文件
                    init_file.touch(exist_ok=True)
                    print(f"创建包初始化文件: {init_file}")

    def _test_run_file(self, file_path: Path):
        """
        测试运行文件，检查是否能成功执行
        """
        try:
            # 为GUI应用设置离线环境变量
            env = os.environ.copy()
            env['QT_QPA_PLATFORM'] = 'offscreen'

            # 动态构造PYTHONPATH，确保项目src目录在Python路径中
            src_path = self.project_root_path / "src"
            if src_path.exists():
                if 'PYTHONPATH' in env:
                    env['PYTHONPATH'] = f"{src_path};{env['PYTHONPATH']}"
                else:
                    env['PYTHONPATH'] = str(src_path)

            # 同时也将项目根目录添加到PYTHONPATH
            project_root_str = str(self.project_root_path)
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{project_root_str};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = project_root_str

            # 确保在项目根目录下运行，使用虚拟环境
            venv_path = self.project_root_path / "venv"
            if venv_path.exists():
                if os.name == 'nt':  # Windows
                    python_path = venv_path / "Scripts" / "python.exe"
                else:  # Unix/Linux/macOS
                    python_path = venv_path / "bin" / "python"
            else:
                python_path = sys.executable

            # 确保file_path是相对于项目根目录的路径
            if file_path.is_absolute():
                try:
                    relative_path = file_path.relative_to(self.project_root_path)
                except ValueError:
                    # 如果file_path不在项目根目录下，使用原路径
                    relative_path = file_path
            else:
                relative_path = file_path

            result = subprocess.run([str(python_path), str(relative_path)],
                                  capture_output=True,
                                  text=True,
                                  timeout=30,
                                  cwd=str(self.project_root_path),
                                  env=env)

            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "运行超时（30秒）"
        except Exception as e:
            return False, str(e)

    async def _fix_code_with_ai(self, file_path: Path, error_msg: str):
        """
        使用AI修复代码错误
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            current_code = f.read()

        # 检测符号不匹配问题
        symbol_issues = self._detect_symbol_mismatches(error_msg, file_path)

        # 检查是否是导入或符号相关的错误，如果是，尝试读取相关文件
        related_files_content = ""
        if "cannot import" in error_msg or "ImportError" in error_msg or "has no attribute" in error_msg or "not defined" in error_msg:
            # 尝试找出相关的文件并读取它们的内容
            import_match = re.search(r"from ([\w.]+) import|import ([\w.]+)", error_msg)
            if import_match:
                module_name = next(filter(None, import_match.groups()), None)
                if module_name:
                    # 尝试找到对应的文件
                    module_parts = module_name.split('.')
                    search_path = self.project_root_path
                    for part in module_parts:
                        search_path = search_path / part

                    # 查找对应的.py文件
                    possible_paths = [
                        self.project_root_path / f"{module_name.replace('.', '/')}.py",
                        self.project_root_path / f"{module_name.replace('.', '/')}" / "__init__.py",
                        self.project_root_path / "src" / f"{module_name.replace('.', '/')}.py",
                        self.project_root_path / "src" / f"{module_name.replace('.', '/')}" / "__init__.py"
                    ]

                    for path in possible_paths:
                        if path.exists():
                            with open(path, 'r', encoding='utf-8') as f:
                                related_content = f.read()
                                related_files_content += f"\n\nRelated file ({path}): ```python\n{related_content}\n```"
                            break

        # 检查是否是循环导入错误
        is_circular_import = False
        current_file_module = str(file_path.relative_to(self.project_root_path)).replace('/', '.').replace('\\', '.').replace('.py', '')
        if "ImportError" in error_msg and current_file_module in error_msg:
            is_circular_import = True
            print(f"检测到循环导入错误: 文件 {current_file_module} 试图导入自身")

        # 构造修复提示，增加全局依赖自检指导
        fix_prompt = f"""
以下Python文件运行时出现错误：

文件内容：
```python
{current_code}
```

{related_files_content}

错误信息：
{error_msg}

符号不匹配分析：
{symbol_issues}

请分析错误原因并修复代码，确保修复后的代码能够正常运行。特别注意：
1. 检查所有必要的导入语句是否完整（如 import sys, import os, import QApplication 等）
2. 检查变量作用域问题（如 UnboundLocalError 通常是由于局部变量和全局变量混淆导致）
3. 检查条件分支中的变量定义是否完整
4. 确保所有使用的变量在使用前已定义
5. 检查是否缺少必要的模块导入（如 sys, os, QApplication 等）
6. 如果是导入错误，请检查相关模块中定义的类名、函数名是否与导入语句匹配
7. 检查拼写错误或命名不一致问题
8. 根据符号不匹配分析的结果，修正类名、函数名或导入语句
9. 如果是模块导入错误，请检查是否需要使用绝对导入路径，或项目结构是否正确
10. 请检查是否需要调整模块搜索路径，并考虑项目 src/ 结构的层级关系
11. 严禁在文件中 import 该文件自身定义的类或函数。如果你发现报错提示缺失某个类，请检查是否是由于该类在当前文件中定义的位置不对，或者是因为循环引用导致的，绝对禁止通过 import 自己来修复！
12. 如果是循环导入问题，请重新组织代码结构，将相互依赖的模块分离到不同的文件中

请只返回修复后的完整代码，不要包含额外的解释。
"""

        response = await self.ai_provider.generate_response(fix_prompt)
        if response["success"]:
            fixed_code = response["content"]

            # 提取代码块
            if "```python" in fixed_code:
                start_idx = fixed_code.find("```python") + len("```python")
                end_idx = fixed_code.find("```", start_idx)
                if end_idx != -1:
                    fixed_code = fixed_code[start_idx:end_idx]
                else:
                    # 如果找不到结束标记，取从开始标记之后的所有内容
                    fixed_code = fixed_code[start_idx:]

            return fixed_code
        else:
            # 如果AI修复失败，返回原始代码
            return current_code

    def _check_global_dependencies(self, code: str) -> list:
        """
        检查全局依赖是否完整
        """
        missing_deps = []

        # 检查常见依赖
        if 'QApplication' in code and 'from PyQt5.QtWidgets import' not in code and 'import PyQt5' not in code:
            missing_deps.append('PyQt5')

        if 'sys.' in code or 'sys ' in code or 'sys\n' in code and 'import sys' not in code:
            missing_deps.append('sys')

        if 'os.' in code or 'os ' in code or 'os\n' in code and 'import os' not in code:
            missing_deps.append('os')

        if 'import cv2' not in code and ('cv2.' in code or 'cv2 ' in code):
            missing_deps.append('opencv-python')

        if 'import numpy' not in code and ('np.' in code or 'numpy' in code):
            missing_deps.append('numpy')

        return missing_deps

    def _detect_symbol_mismatches(self, error_msg: str, file_path: Path) -> str:
        """
        检测符号不匹配问题，如导入的类名与实际定义的类名不一致
        """
        symbol_issues = ""

        # 检查是否是属性或符号不存在的错误
        import_error_match = re.search(r"cannot import name '(\w+)' from '(.*)'", error_msg)
        if import_error_match:
            symbol_name = import_error_match.group(1)
            module_path = import_error_match.group(2)

            # 尝试找到该模块的实际定义
            # 构建可能的文件路径
            module_file_path = module_path.replace('.', '/')
            possible_paths = [
                self.project_root_path / f"{module_file_path}.py",
                self.project_root_path / f"{module_file_path}" / "__init__.py",
                self.project_root_path / "src" / f"{module_file_path}.py",
                self.project_root_path / "src" / f"{module_file_path}" / "__init__.py"
            ]

            for path in possible_paths:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 查找所有类定义
                        class_matches = re.findall(r'class\s+(\w+)', content)
                        if class_matches:
                            symbol_issues += f"\n在文件 {path} 中找到以下类定义: {', '.join(class_matches)}"
                            symbol_issues += f"\n但尝试导入的类名为: {symbol_name}"
                            symbol_issues += f"\n可能需要更正导入语句或类名。"
                        break

        # 检查是否有属性不存在的错误
        attr_error_match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_msg)
        if attr_error_match:
            class_name = attr_error_match.group(1)
            attr_name = attr_error_match.group(2)
            symbol_issues += f"\n'{class_name}' 类没有 '{attr_name}' 属性。"

        return symbol_issues

    def _construct_prompt(self, task: Task, current_content: str) -> str:
        """
        构造发送给AI的Prompt
        """
        prompt = f"""
你是一个专业的软件工程师，正在实现一个项目的一部分。

## 项目全局方案
{self.project_spec.architecture_proposal}

## 任务信息
- 任务标题: {task.title}
- 任务描述: {task.description}
- 技术要求: {task.technical_requirement}
- 目标路径: {task.target_path}
- 验收标准: {task.verification}

## 当前文件内容
```{self._get_file_extension(task.target_path)}
{current_content}
```

## 任务指令
请根据以上信息，完善或替换当前文件的内容。你需要：
1. 实现任务描述中提到的功能
2. 遵循技术要求中的约束
3. 确保代码满足验收标准
4. 保持代码风格与现有代码一致
5. 如果有依赖其他模块，请确保接口兼容

请只返回代码内容，不要包含额外的解释。
"""
        return prompt

    def _get_file_extension(self, file_path: str) -> str:
        """
        获取文件扩展名，用于代码块标记
        """
        suffix = Path(file_path).suffix
        if suffix:
            return suffix[1:]  # 去掉点号
        return ""

    def _extract_code_from_response(self, response: Dict[str, Any], original_content: str) -> str:
        """
        从AI响应中提取代码内容
        """
        # 尝试从响应中提取代码
        content = response.get("content", "")

        # 如果响应包含代码块标记，则提取代码块内的内容
        if "```" in content:
            # 找到第一个和最后一个代码块标记
            start_idx = content.find("```")
            end_idx = content.rfind("```")

            if start_idx != -1 and end_idx != -1 and start_idx != end_idx:
                # 提取代码块内容
                code_block = content[start_idx:end_idx+3]

                # 找到代码语言标记后的第一行
                first_newline = code_block.find('\n')
                if first_newline != -1:
                    extracted_code = code_block[first_newline+1:-3]  # 去掉开头的语言标记和结尾的 ```

                    # 检查是否包含原始内容的头部信息（如import等）
                    original_lines = original_content.split('\n')

                    # 保留原始文件的头部（如import语句、编码声明等）
                    preserved_header = []
                    for line in original_lines:
                        stripped_line = line.strip()
                        if (stripped_line.startswith("#") and ("coding:" in stripped_line or "encoding:" in stripped_line)) or \
                           stripped_line.startswith("import ") or \
                           stripped_line.startswith("from ") or \
                           stripped_line.startswith("#!/usr/bin") or \
                           stripped_line.startswith("<?php") or \
                           stripped_line.startswith("/*") or \
                           stripped_line.startswith("//"):
                            preserved_header.append(line)
                        else:
                            # 遇到非头部内容就停止
                            if not stripped_line.startswith("#") and stripped_line:
                                break
                            preserved_header.append(line)

                    # 组合保留的头部和AI生成的内容
                    if preserved_header:
                        # 检查AI生成的代码是否已经包含了头部信息
                        extracted_lines = extracted_code.split('\n')
                        ai_has_imports = any(line.strip().startswith(("import ", "from ")) for line in extracted_lines[:10])

                        if not ai_has_imports:
                            final_content = '\n'.join(preserved_header) + '\n' + extracted_code
                        else:
                            final_content = extracted_code
                    else:
                        final_content = extracted_code

                    return final_content.strip()

        # 如果没有找到代码块，则返回原始响应内容
        return content.strip()

    def _write_code_to_file(self, target_path: Path, new_code: str, original_content: str):
        """
        将生成的代码写入文件，保留必要的头部信息
        """
        # 读取原始文件的头部信息（如import语句、编码声明等）
        original_lines = original_content.split('\n')
        header_lines = []

        for line in original_lines:
            stripped_line = line.strip()
            # 识别头部信息
            if (stripped_line.startswith("#") and ("coding:" in stripped_line or "encoding:" in stripped_line)) or \
               stripped_line.startswith("import ") or \
               stripped_line.startswith("from ") or \
               stripped_line.startswith("#!/usr/bin") or \
               stripped_line.startswith("<?php") or \
               stripped_line.startswith("/*") or \
               stripped_line.startswith("//"):
                header_lines.append(line)
            else:
                # 遇到非头部内容就停止
                if not stripped_line.startswith("#") and stripped_line:
                    break
                header_lines.append(line)

        # 组合头部和新代码
        if header_lines:
            # 检查新代码是否已经包含了头部信息
            new_lines = new_code.split('\n')
            has_imports_in_new_code = any(line.strip().startswith(("import ", "from ")) for line in new_lines[:10])

            if not has_imports_in_new_code:
                final_content = '\n'.join(header_lines) + '\n' + new_code
            else:
                final_content = new_code
        else:
            final_content = new_code

        # 写入文件
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

    def _update_development_log(self, task: Task):
        """
        更新开发日志，在对应条目后追加'[COMPLETED BY CODER]'字样
        """
        dev_log_path = self.project_root_path / "DEVELOPMENT_LOG.md"

        if not dev_log_path.exists():
            print(f"警告: 开发日志不存在: {dev_log_path}")
            return

        with open(dev_log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找对应任务的条目并更新
        task_marker = f"### 任务: {task.title}"
        completed_marker = "[COMPLETED BY CODER]"

        # 检查是否已经标记为完成
        if completed_marker in content[content.find(task_marker):content.find(task_marker)+content[content.find(task_marker):].find('\n### ')]:
            # 已经完成，跳过
            return

        # 在任务标题后插入完成标记
        updated_content = content.replace(
            f"### 任务: {task.title}",
            f"### 任务: {task.title}\n- 状态: {completed_marker}",
            1
        )

        with open(dev_log_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)