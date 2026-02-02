#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式需求收集器
通过友好的问答界面收集用户项目需求
"""

import sys
from typing import Dict, List, Optional
from pathlib import Path


class InteractiveCollector:
    """交互式需求收集器"""
    
    def __init__(self):
        self.requirements = {}
    
    def print_header(self):
        """打印欢迎界面"""
        print("=" * 60)
        print("Vibe Coding 架构师 Agent - 交互式需求收集")
        print("=" * 60)
        print("请回答以下问题，我将为您设计完美的项目架构！")
        print()
    
    def ask_question(self, prompt: str, required: bool = True, default: Optional[str] = None) -> str:
        """询问单个问题"""
        while True:
            if default:
                user_input = input(f"{prompt} (默认: {default}): ").strip()
                if not user_input:
                    return default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if user_input:
                return user_input
            elif not required:
                return ""
            else:
                print("此问题为必填项，请重新输入。")
    
    def ask_multiple_choice(self, prompt: str, options: List[str]) -> str:
        """多选题"""
        print(f"\n{prompt}")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        while True:
            try:
                choice = input("请选择 (输入数字): ").strip()
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(options):
                        return options[index]
                    else:
                        print("请输入有效的数字范围")
                else:
                    print("请输入数字")
            except ValueError:
                print("请输入有效的数字")
    
    def ask_checkbox(self, prompt: str, options: List[str]) -> List[str]:
        """多选框"""
        print(f"\n{prompt} (可多选，用逗号分隔)")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        while True:
            try:
                choice = input("请选择 (输入数字，用逗号分隔，如: 1,3,5): ").strip()
                if not choice:
                    return []
                
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                selected = []
                valid = True
                
                for index in indices:
                    if 0 <= index < len(options):
                        selected.append(options[index])
                    else:
                        valid = False
                        break
                
                if valid:
                    return selected
                else:
                    print("请输入有效的数字范围")
            except ValueError:
                print("请输入有效的数字，用逗号分隔")
    
    def collect_basic_info(self) -> Dict[str, str]:
        """收集基本信息"""
        print("\n基本信息")
        print("-" * 30)
        
        try:
            project_name = self.ask_question("项目名称")
            if not project_name:
                project_name = "未命名项目"
        except (EOFError, KeyboardInterrupt):
            project_name = "未命名项目"
            
        try:
            project_description = self.ask_question("项目描述")
            if not project_description:
                project_description = "项目描述待补充"
        except (EOFError, KeyboardInterrupt):
            project_description = "项目描述待补充"
            
        try:
            author = self.ask_question("作者姓名", required=False)
        except (EOFError, KeyboardInterrupt):
            author = "开发者"
        
        return {
            "project_name": project_name,
            "description": project_description,
            "author": author or "开发者"
        }
    
    def collect_tech_info(self) -> Dict[str, str]:
        """收集技术信息"""
        print("\n技术栈选择")
        print("-" * 30)
        
        # 编程语言
        languages = ["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "其他"]
        language = self.ask_multiple_choice("主要编程语言", languages)
        
        # 项目类型
        project_types = [
            "Web API (REST/GraphQL)",
            "Web应用 (前端)",
            "移动应用",
            "桌面应用", 
            "CLI工具",
            "数据处理/分析",
            "机器学习/AI",
            "微服务",
            "其他"
        ]
        project_type = self.ask_multiple_choice("项目类型", project_types)
        
        # 框架选择 (根据语言)
        frameworks = {
            "Python": ["Django", "FastAPI", "Flask", "Streamlit", "Jupyter", "无"],
            "JavaScript": ["Express.js", "React", "Vue.js", "Angular", "Node.js", "无"],
            "TypeScript": ["Express.js", "React", "Vue.js", "Angular", "Node.js", "NestJS", "无"],
            "Java": ["Spring Boot", "Spring MVC", "Maven", "Gradle", "无"],
            "Go": ["Gin", "Echo", "Fiber", "标准库", "无"],
            "其他": ["请手动指定"]
        }
        
        available_frameworks = frameworks.get(language, ["请手动指定"])
        framework = self.ask_multiple_choice("主要框架", available_frameworks)
        
        # 数据库选择
        databases = ["PostgreSQL", "MySQL", "MongoDB", "SQLite", "Redis", "无数据库", "其他"]
        database = self.ask_multiple_choice("数据库", databases)
        
        return {
            "language": language,
            "project_type": project_type,
            "framework": framework,
            "database": database
        }
    
    def collect_features(self) -> List[str]:
        """收集功能需求"""
        print("\n功能需求")
        print("-" * 30)
        
        # 根据项目类型提供不同的功能选项
        common_features = [
            "用户认证和授权",
            "数据库CRUD操作", 
            "API接口文档",
            "单元测试",
            "日志记录",
            "配置管理",
            "错误处理",
            "性能监控",
            "部署配置"
        ]
        
        web_features = [
            "前端页面",
            "响应式设计",
            "SEO优化",
            "文件上传",
            "实时通信(WebSocket)",
            "缓存机制"
        ]
        
        api_features = [
            "RESTful API",
            "GraphQL支持",
            "API版本控制",
            "限流保护",
            "API网关",
            "微服务架构"
        ]
        
        ai_features = [
            "模型训练",
            "数据预处理",
            "模型推理",
            "可视化展示",
            "实验管理"
        ]
        
        # 提供所有功能让用户选择
        all_features = common_features + web_features + api_features + ai_features
        selected_features = self.ask_checkbox("请选择需要的功能", all_features)
        
        # 如果用户有其他需求
        other_features = self.ask_question("其他功能需求 (用逗号分隔)", required=False)
        if other_features:
            selected_features.extend([f.strip() for f in other_features.split(',')])
        
        return selected_features
    
    def collect_deployment(self) -> Dict[str, str]:
        """收集部署需求"""
        print("\n部署需求")
        print("-" * 30)
        
        platforms = [
            "Docker容器",
            "云服务 (AWS/Azure/GCP)",
            "传统服务器",
            "本地部署",
            "暂不考虑部署"
        ]
        platform = self.ask_multiple_choice("部署平台", platforms)
        
        environments = ["开发环境", "测试环境", "生产环境", "全部环境"]
        env = self.ask_checkbox("需要的环境配置", environments)
        
        return {
            "platform": platform,
            "environments": ", ".join(env) if env else "无特殊要求"
        }
    
    def collect_additional_info(self) -> str:
        """收集其他信息"""
        print("\n补充说明")
        print("-" * 30)
        
        return self.ask_question("其他特殊需求或说明", required=False)
    
    def generate_requirement_summary(self, data: Dict) -> str:
        """生成需求摘要"""
        summary = f"""
项目需求摘要:

基本信息
- 项目名称: {data['basic']['project_name']}
- 项目描述: {data['basic']['description']}
- 作者: {data['basic']['author']}

技术栈
- 编程语言: {data['tech']['language']}
- 项目类型: {data['tech']['project_type']}
- 主要框架: {data['tech']['framework']}
- 数据库: {data['tech']['database']}

功能需求
{chr(10).join(f'- {feature}' for feature in data['features'])}

部署需求
- 部署平台: {data['deployment']['platform']}
- 环境配置: {data['deployment']['environments']}
"""

        if data['additional']:
            summary += f"""
补充说明
{data['additional']}
"""
        
        return summary.strip()
    
    def collect(self) -> str:
        """收集所有需求"""
        self.print_header()
        
        # 收集各个部分的信息
        basic_info = self.collect_basic_info()
        tech_info = self.collect_tech_info()
        features = self.collect_features()
        deployment = self.collect_deployment()
        additional = self.collect_additional_info()
        
        # 整理数据
        data = {
            'basic': basic_info,
            'tech': tech_info,
            'features': features,
            'deployment': deployment,
            'additional': additional
        }
        
        # 生成摘要
        summary = self.generate_requirement_summary(data)
        
        # 确认信息
        print("\n" + "=" * 60)
        print("需求确认")
        print("=" * 60)
        print(summary)
        
        confirm = input("\n确认以上需求正确吗？(y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            print("\n需求收集完成，正在生成项目架构...")
            return summary
        else:
            print("\n需求收集已取消。")
            sys.exit(0)


def main():
    """主函数"""
    collector = InteractiveCollector()
    requirement = collector.collect()
    return requirement


if __name__ == "__main__":
    try:
        requirement = main()
        print(f"\n生成需求摘要:\n{requirement}")
    except KeyboardInterrupt:
        print("\n\n用户取消操作。")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        sys.exit(1)