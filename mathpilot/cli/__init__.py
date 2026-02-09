"""CLI module - Entry point and command routing."""

from typing import Optional
import typer

from mathpilot.utils import get_logger

app = typer.Typer(help="Scientific workflow assistant")
logger = get_logger(__name__)


@app.command()
def implement(
    task: str = typer.Argument(..., help="Natural language task (e.g., 'Kalman filter')"),
    paper_url: Optional[str] = typer.Option(None, help="Specific paper URL (arXiv)"),
    output_dir: str = typer.Option("./mathpilot_projects", help="Output directory"),
    execute: bool = typer.Option(False, "--execute", help="Execute generated code"),
) -> None:
    """Generate an implementation plan and code for a scientific algorithm."""
    logger.info(f"Task: {task}")
    logger.info(f"Output: {output_dir}")
    if execute:
        logger.warning("Code execution enabled (experimental)")
    typer.echo("MathPilot implementation plan coming soon...")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for arXiv"),
    max_results: int = typer.Option(5, help="Max papers to retrieve"),
) -> None:
    """Search for papers on arXiv."""
    logger.info(f"Searching: {query}")
    typer.echo("Paper search coming soon...")


@app.command()
def workspace(
    action: str = typer.Argument(..., help="list, delete, or run"),
) -> None:
    """Manage generated projects and workspaces."""
    logger.info(f"Workspace action: {action}")
    typer.echo("Workspace management coming soon...")


@app.callback()
def main(
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
) -> None:
    """Scientific workflow assistant powered by LLM."""
    if debug:
        logger.setLevel("DEBUG")
        logger.debug("Debug mode enabled")


if __name__ == "__main__":
    app()
