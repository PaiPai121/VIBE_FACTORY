from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class FlexibilityEnum(str, Enum):
    FIXED = "fixed"
    FLEXIBLE = "flexible"


class Task(BaseModel):
    """
    任务模型，定义了需要完成的具体任务
    """
    id: int = Field(..., description="任务唯一标识符")
    title: str = Field(..., description="任务标题")
    description: str = Field(..., description="任务详细描述")
    target_path: str = Field(..., description="目标路径 - PnC准则中的物理路径")
    verification: str = Field(..., description="验收标准 - PnC准则中的验证步骤")
    flexibility: FlexibilityEnum = Field(..., description="灵活性 - 限定值为 'fixed' 或 'flexible'")
    technical_requirement: str = Field(default="", description="技术要求 - 具体的实现细节和约束")
    dependencies: Optional[List[int]] = Field(default=None, description="依赖的任务ID列表")


class ProjectSpec(BaseModel):
    """
    项目规格模型，定义了整个项目的规范
    """
    project_name: str = Field(..., description="项目名称")
    description: str = Field(..., description="项目描述")
    version: str = Field(default="1.0.0", description="项目版本 - 支持版本化")
    tasks: List[Task] = Field(..., description="项目任务列表")
    architecture_proposal: str = Field(default="", description="架构提案 - 辩论后的整体架构设计方案，需包含目录划分理由和核心技术选型决策树")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")