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
    import os
    from rich.console import Console
    from mathpilot.search import ArxivClient
    from mathpilot.parser import parse_paper
    from mathpilot.planner import generate_plan

    console = Console()
    
    # 1. Get PDF path
    pdf_path = None
    paper_title = "Unknown Paper"
    
    if os.path.exists(paper_id) and paper_id.endswith(".pdf"):
        pdf_path = paper_id
        paper_title = os.path.basename(paper_id).replace(".pdf", "")
        console.print(f"[green]Using local PDF: {pdf_path}[/green]")
    else:
        # Assume arXiv ID
        with console.status(f"[bold blue]Resolving arXiv paper: {paper_id}..."):
            client = ArxivClient()
            papers = client.search(paper_id)
            if not papers:
                console.print(f"[red]Paper not found on arXiv: {paper_id}[/red]")
                raise typer.Exit(code=1)
            
            paper = papers[0]
            paper_title = paper.title
            
            cache_dir = os.path.expanduser("~/.mathpilot/cache")
            pdf_path = os.path.join(cache_dir, f"{paper.id}.pdf")
            
            if not os.path.exists(pdf_path):
                console.print(f"Downloading PDF to {pdf_path}...")
                if paper.pdf_url:
                    client.download_pdf(str(paper.pdf_url), pdf_path)
                else:
                    console.print("[red]No PDF URL found for paper.[/red]")
                    raise typer.Exit(code=1)
            else:
                console.print(f"[dim]Using cached PDF: {pdf_path}[/dim]")

    # 2. Parse PDF
    with console.status(f"[bold yellow]Parsing paper content (this may take a minute)..."):
        try:
            parsed_paper = parse_paper(pdf_path, paper_title)
            console.print(f"[green]Successfully parsed {len(parsed_paper.algorithms)} algorithm(s).[/green]")
        except Exception as e:
            console.print(f"[red]Parsing failed: {e}[/red]")
            raise typer.Exit(code=1)

    # 3. Generate Plan
    # Only plan for the first algorithm for now
    if not parsed_paper.algorithms:
        console.print("[red]No algorithms found in paper.[/red]")
        raise typer.Exit(code=1)
        
    algorithm = parsed_paper.algorithms[0]
    console.print(f"Generating plan for algorithm: [bold]{algorithm.name}[/bold]")
    
    with console.status(f"[bold magenta]Generating implementation plan..."):
        try:
            plan = generate_plan(paper_title, algorithm)
        except Exception as e:
            console.print(f"[red]Planning failed: {e}[/red]")
            raise typer.Exit(code=1)

    # 4. Save Plan
    if not output:
        output = f"plan_{algorithm.name.lower().replace(' ', '_')}.json"
    
    with open(output, "w") as f:
        f.write(plan.model_dump_json(indent=2))
        
    console.print(f"[bold green]Plan saved to: {output}[/bold green]")
    
    # Display summary
    console.print("\n[bold underline]Implementation Steps:[/bold underline]")
    for step in plan.steps:
        console.print(f"[cyan]{step.step_id}[/cyan]: {step.title}")

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
