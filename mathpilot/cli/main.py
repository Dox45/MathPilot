import typer
from typing import Optional
from mathpilot.utils.config import Config
from mathpilot.utils import get_logger

app = typer.Typer(
    name="mathpilot",
    help="Scientific workflow assistant - AI-powered algorithm implementation",
    add_completion=False,
)
logger = get_logger("cli")
config = Config()

@app.command()
def search(
    query: str = typer.Argument(..., help="Natural language query or keywords"),
    max_results: int = typer.Option(5, help="Maximum number of papers to retrieve"),
    download: bool = typer.Option(False, help="Download PDFs of found papers"),
):
    """
    Search for research papers on arXiv.
    """
    from mathpilot.search import ArxivClient
    from rich.console import Console
    from rich.table import Table

    console = Console()
    
    with console.status(f"[bold green]Searching for: {query}..."):
        client = ArxivClient(max_results=max_results)
        papers = client.search(query=query)

    if not papers:
        console.print("[yellow]No papers found.[/yellow]")
        return

    table = Table(title=f"ArXiv Search Results: {query}")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Authors", style="green")
    table.add_column("Published", style="blue")

    for paper in papers:
        table.add_row(
            paper.id,
            paper.title,
            ", ".join(paper.authors[:3]) + ("..." if len(paper.authors) > 3 else ""),
            paper.published.strftime("%Y-%m-%d")
        )

    console.print(table)
    
    if download:
        console.print("[dim]Download functionality not yet implemented.[/dim]")

@app.command()
def plan(
    paper_id: str = typer.Argument(..., help="arXiv ID or URL of the paper"),
    output: Optional[str] = typer.Option(None, help="Output path for the plan"),
):
    """
    Generate an implementation plan from a paper.
    """
    typer.echo(f"Planning implementation for paper: {paper_id}")
    # TODO: Connect to planner module

@app.command()
def generate(
    plan_path: str = typer.Argument(..., help="Path to the plan file"),
    output_dir: str = typer.Option("./workspace", help="Directory to save generated code"),
):
    """
    Generate Python code from an implementation plan.
    """
    typer.echo(f"Generating code from: {plan_path} to {output_dir}")
    # TODO: Connect to generator module

@app.command()
def run(
    script_path: str = typer.Argument(..., help="Path to the python script"),
):
    """
    Execute a generated script safely.
    """
    typer.echo(f"Running script: {script_path}")
    # TODO: Connect to executor module

if __name__ == "__main__":
    app()
