"""Manage generated projects and workspace organization."""

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


@dataclass
class Project:
    """Generated implementation project."""

    id: str
    name: str
    task: str
    paper_title: str
    created_at: datetime
    root_dir: Path
    workflow_file: Path
    code_dir: Path
    logs_dir: Path


def create_project(
    name: str,
    task: str,
    paper_title: str,
    base_dir: str = "~/mathpilot_projects",
) -> Project:
    """
    Create new project workspace.

    Creates directory structure:
        project_name/
        ├── workflow.yaml
        ├── src/
        │   ├── __init__.py
        │   ├── main.py
        │   └── ...
        ├── tests/
        ├── data/
        └── logs/
    """
    # TODO: Create directories
    # TODO: Initialize workflow.yaml
    # TODO: Return Project object
    pass


def load_project(project_path: str) -> Project:
    """Load existing project from disk."""
    # TODO: Load workflow.yaml
    # TODO: Validate structure
    pass


def list_projects(base_dir: str = "~/mathpilot_projects") -> list[Project]:
    """List all generated projects."""
    # TODO: Scan directory
    # TODO: Load metadata
    pass


def archive_project(project: Project) -> None:
    """Archive a project."""
    # TODO: Create tarball
    # TODO: Move to archive directory
    pass
