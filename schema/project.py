from pydantic import BaseModel, Field
from typing import List, Optional


class Task(BaseModel):
    """
    Represents a single task in the project specification.
    Each task must include a target path and verification criteria.
    """
    id: str = Field(..., description="Unique identifier for the task")
    title: str = Field(..., description="Brief title of the task")
    description: str = Field(..., description="Detailed description of what needs to be done")
    target_path: str = Field(..., description="The specific file path where the implementation should be placed")
    verification: str = Field(..., description="Acceptance criteria to verify the task is completed correctly")
    dependencies: Optional[List[str]] = Field(default=[], description="List of task IDs this task depends on")
    priority: Optional[str] = Field(default="medium", description="Task priority: high/medium/low")
    status: Optional[str] = Field(default="pending", description="Task status: pending/in_progress/completed")
    metadata: Optional[dict] = Field(default={}, description="Additional metadata for the task")


class ProjectSpec(BaseModel):
    """
    Main project specification model that contains all tasks and metadata.
    """
    project_name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Overall description of the project")
    version: str = Field(default="1.0.0", description="Project version")
    tasks: List[Task] = Field(..., description="List of tasks to complete the project")
    created_at: Optional[str] = Field(default=None, description="Timestamp when the spec was created")
    author: Optional[str] = Field(default="开发者", description="Project author")
    tech_stack: Optional[dict] = Field(default={}, description="Technology stack configuration")
    config: Optional[dict] = Field(default={}, description="Project configuration")
    metadata: Optional[dict] = Field(default={}, description="Additional metadata")