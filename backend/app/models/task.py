"""
Task Model

Stores action items and tasks extracted from meetings/messages.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum, ForeignKey
from sqlalchemy.sql import func
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Task status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """Task model for action items."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Assignment
    assigned_to = Column(String(255), nullable=True)
    assigned_by = Column(String(255), nullable=True)
    
    # Status
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Timing
    deadline = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Source (where the task came from)
    source_meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    source_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    source_context = Column(Text, nullable=True)  # Original quote/context
    
    # Proposed solutions (for technical tasks)
    proposed_solutions = Column(JSON, nullable=True)
    """
    Proposed solutions format:
    [
        {
            "title": "Quick fix",
            "description": "Patch the bug with minimal changes",
            "estimated_time": "30 minutes",
            "pros": ["Fast", "Low risk"],
            "cons": ["Technical debt"]
        },
        ...
    ]
    """
    
    selected_solution = Column(Integer, nullable=True)  # Index of chosen solution
    
    # Tags
    tags = Column(JSON, nullable=True)  # ["bug", "feature", "documentation"]
    
    # Related GitHub/GitLab
    repository = Column(String(255), nullable=True)
    issue_url = Column(String(500), nullable=True)
    pr_url = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"
