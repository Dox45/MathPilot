"""Manage generated projects and workspace organization."""

import shutil
import yaml
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from mathpilot.utils import get_logger

logger = get_logger("workspace")

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
    base_path = Path(base_dir).expanduser()
    project_dir = base_path / name
    
    if project_dir.exists():
        logger.warning(f"Project directory already exists: {project_dir}")
        # Append timestamp to make unique or raise error? 
        # For now, let's assume we want a fresh start if it exists or user handles naming
        # But to be safe, let's error if strictly duplicate? 
        # Actually, let's just use it or fail.
        # Let's ensure we don't overwrite blindly without warning.
        pass

    # Create directories
    src_dir = project_dir / "src"
    tests_dir = project_dir / "tests"
    data_dir = project_dir / "data"
    logs_dir = project_dir / "logs"

    for d in [src_dir, tests_dir, data_dir, logs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Init files
    (src_dir / "__init__.py").touch()
    
    workflow_file = project_dir / "workflow.yaml"
    
    project_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    project = Project(
        id=project_id,
        name=name,
        task=task,
        paper_title=paper_title,
        created_at=datetime.now(),
        root_dir=project_dir,
        workflow_file=workflow_file,
        code_dir=src_dir,
        logs_dir=logs_dir
    )

    # Save metadata
    metadata = asdict(project)
    # Convert Path objects to strings for YAML
    for key, value in metadata.items():
        if isinstance(value, Path):
            metadata[key] = str(value)
        elif isinstance(value, datetime):
            metadata[key] = value.isoformat()

    with open(workflow_file, "w") as f:
        yaml.dump(metadata, f)
        
    logger.info(f"Created project '{name}' at {project_dir}")
    return project


def load_project(project_path: str) -> Project:
    """Load existing project from disk."""
    path = Path(project_path).expanduser()
    workflow_file = path / "workflow.yaml"
    
    if not workflow_file.exists():
        raise FileNotFoundError(f"Not a valid project (missing workflow.yaml): {path}")
        
    with open(workflow_file, "r") as f:
        metadata = yaml.safe_load(f)
        
    # Reconstruct Project object
    return Project(
        id=metadata["id"],
        name=metadata["name"],
        task=metadata["task"],
        paper_title=metadata["paper_title"],
        created_at=datetime.fromisoformat(metadata["created_at"]),
        root_dir=Path(metadata["root_dir"]),
        workflow_file=Path(metadata["workflow_file"]),
        code_dir=Path(metadata["code_dir"]),
        logs_dir=Path(metadata["logs_dir"])
    )


def list_projects(base_dir: str = "~/mathpilot_projects") -> List[Project]:
    """List all generated projects."""
    base_path = Path(base_dir).expanduser()
    if not base_path.exists():
        return []
        
    projects = []
    for item in base_path.iterdir():
        if item.is_dir() and (item / "workflow.yaml").exists():
            try:
                projects.append(load_project(str(item)))
            except Exception as e:
                logger.warning(f"Failed to load project at {item}: {e}")
                
    return sorted(projects, key=lambda p: p.created_at, reverse=True)


def archive_project(project: Project) -> None:
    """Archive a project."""
    archive_dir = project.root_dir.parent / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    archive_name = shutil.make_archive(
        str(archive_dir / project.id),
        'zip',
        root_dir=project.root_dir
    )
    
    logger.info(f"Archived project to {archive_name}")
    # Optional: remove original?
    # shutil.rmtree(project.root_dir)
