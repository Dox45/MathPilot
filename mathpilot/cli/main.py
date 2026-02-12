import typer
from typing import Optional
from pathlib import Path
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
        
    console.print(f"[dim]Found {len(papers)} papers.[/dim]")
    console.print("[dim italic]Tip: Use quotes for exact match (e.g. \"Attention Is All You Need\") or prefixes (ti:, au:).[/dim italic]\n")

    table = Table(title=f"ArXiv Search Results: {query}", padding=(0, 1), show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta", ratio=3)
    table.add_column("Authors", style="green", ratio=2)
    table.add_column("Published", style="blue", no_wrap=True)

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
    
    return papers

def _plan_impl(paper_id: str, output: Optional[str] = None):
    """Internal implementation of plan workflow."""
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
            os.makedirs(cache_dir, exist_ok=True)
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
            plan_obj = generate_plan(paper_title, algorithm)
        except Exception as e:
            console.print(f"[red]Planning failed: {e}[/red]")
            raise typer.Exit(code=1)

    # 4. Save Plan
    if not output:
        output = f"plan_{algorithm.name.lower().replace(' ', '_')}.json"
    
    with open(output, "w") as f:
        f.write(plan_obj.model_dump_json(indent=2))
        
    console.print(f"[bold green]Plan saved to: {output}[/bold green]")
    
    # Display summary
    console.print("\n[bold underline]Implementation Steps:[/bold underline]")
    for step in plan_obj.steps:
        console.print(f"[cyan]{step.step_id}[/cyan]: {step.title}")
        
    return output

@app.command()
def plan(
    paper_id: str = typer.Argument(..., help="arXiv ID or URL of the paper"),
    output: Optional[str] = typer.Option(None, help="Output path for the plan"),
):
    """
    Generate an implementation plan from a paper.
    """
    return _plan_impl(paper_id, output)

def _generate_impl(plan_path: str, project_name: Optional[str] = None, output_dir: str = "~/mathpilot_projects"):
    """Internal implementation of generate workflow."""
    from rich.console import Console
    from mathpilot.planner.models import ImplementationPlan
    from mathpilot.generator import generate_project_code, generate_requirements
    from mathpilot.workspace import create_project

    console = Console()
    
    # 1. Load Plan
    try:
        with open(plan_path, "r") as f:
            plan_json = f.read()
            plan_obj = ImplementationPlan.model_validate_json(plan_json)
        console.print(f"[green]Loaded plan: {plan_obj.paper_title} - {plan_obj.algorithm_name}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to load plan: {e}[/red]")
        raise typer.Exit(code=1)
        
    # 2. Determine Project Name
    if not project_name:
        # Clean up algorithm name for directory
        safe_name = "".join(c if c.isalnum() else "_" for c in plan_obj.algorithm_name)
        project_name = safe_name.lower()
        
    # 3. Create Workspace
    with console.status(f"[bold blue]Creating project workspace: {project_name}..."):
        try:
            project = create_project(
                name=project_name,
                task=plan_obj.summary,
                paper_title=plan_obj.paper_title,
                base_dir=output_dir
            )
            console.print(f"[green]Created project at: {project.root_dir}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to create project: {e}[/red]")
            raise typer.Exit(code=1)
            
    # 4. Generate Code
    with console.status(f"[bold magenta]Generating code (this may take a while)..."):
        try:
            templates = generate_project_code(plan_obj)
            console.print(f"[green]Generated {len(templates)} code files.[/green]")
        except Exception as e:
            console.print(f"[red]Code generation failed: {e}[/red]")
            raise typer.Exit(code=1)
            
    # 5. Write Files
    with console.status(f"[bold yellow]Writing files to disk..."):
        try:
            for filename, template in templates.items():
                file_path = project.code_dir / filename
                with open(file_path, "w") as f:
                    f.write(template.code)
                    
            # Write requirements.txt
            reqs = generate_requirements(templates)
            with open(project.root_dir / "requirements.txt", "w") as f:
                f.write(reqs)
                
            console.print(f"[green]Files written successfully.[/green]")
            
        except Exception as e:
            console.print(f"[red]Failed to write files: {e}[/red]")
            raise typer.Exit(code=1)
            
    console.print(f"\n[bold green]Success! Project generated at: {project.root_dir}[/bold green]")
    console.print(f"  pip install -r requirements.txt")
    console.print(f"  python src/main.py")
    
    return project.root_dir

@app.command()
def generate(
    plan_path: str = typer.Argument(..., help="Path to the plan file"),
    project_name: str = typer.Option(None, help="Name of the project"),
    output_dir: str = typer.Option("~/mathpilot_projects", help="Base directory for projects"),
):
    """
    Generate Python code from an implementation plan.
    """
    return _generate_impl(plan_path, project_name, output_dir)

@app.command()
def run(
    script_path: str = typer.Argument(..., help="Path to the python script"),
    timeout: int = typer.Option(300, help="Execution timeout in seconds"),
):
    """
    Execute a generated script safely.
    """
    from rich.console import Console
    from mathpilot.executor import execute_script, log_execution

    console = Console()
    
    console.print(f"[bold]Executing script: {script_path}[/bold]")
    
    with console.status("Running..."):
        result = execute_script(script_path, timeout=timeout)
        
    if result.success:
        console.print("[bold green]Execution Successful[/bold green]")
        if result.stdout:
            console.print("\n[dim]Output:[/dim]")
            console.print(result.stdout)
    else:
        console.print(f"[bold red]Execution Failed (Exit Code: {result.exit_code})[/bold red]")
        if result.stderr:
            console.print("\n[dim]Error Output:[/dim]")
            console.print(result.stderr)
        if result.stdout:
            console.print("\n[dim]Standard Output:[/dim]")
            console.print(result.stdout)
            
    console.print(f"\n[dim]Time: {result.execution_time:.2f}s[/dim]")
    
    # Log it
    try:
        log_execution(
            workflow_id="manual_run",
            step_id=Path(script_path).stem,
            result=result
        )
        console.print(f"[dim]Log saved.[/dim]")
    except Exception as e:
        console.print(f"[yellow]Failed to save log: {e}[/yellow]")

@app.command()
def interactive():
    """
    Start interactive REPL mode.
    """
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.table import Table
    from pathlib import Path
    from mathpilot.utils.file_browser import (
        get_common_pdf_locations,
        find_pdfs_in_folder,
        select_folder_interactive,
        select_pdf_interactive,
    )
    
    console = Console()
    console.clear()
    console.print(Panel.fit("[bold cyan]MathPilot Interactive Mode[/bold cyan]", border_style="blue"))
    
    while True:
        console.print("\n[bold]Select an action:[/bold]")
        console.print("1. [green]Search ArXiv & Implement[/green]")
        console.print("2. [yellow]Browse for PDF[/yellow]")
        console.print("3. [red]Exit[/red]")
        
        choice = Prompt.ask("Choose option", choices=["1", "2", "3"], default="1")
        
        if choice == "3":
            console.print("Goodbye!")
            break
            
        elif choice == "1":
            query = Prompt.ask("Enter search query")
            papers = search(query=query, max_results=5, download=False)
            
            if papers:
                console.print("\n[bold]Select a paper to implement:[/bold]")
                # Create options 1..N and 0 for cancel
                choices = [str(i) for i in range(1, len(papers) + 1)]
                choices.append("0")
                
                paper_choice = Prompt.ask("Choose paper number (0 to cancel)", choices=choices, default="0")
                
                if paper_choice != "0":
                    selected_paper = papers[int(paper_choice) - 1]
                    console.print(f"[green]Selected: {selected_paper.title}[/green]")
                    
                    if Confirm.ask("Generate implementation plan for this paper?"):
                        try:
                            # Use internal impl to avoid OptionInfo error
                            plan_path = _plan_impl(paper_id=selected_paper.id)
                            
                            if plan_path and Confirm.ask(f"\nPlan saved to {plan_path}. Generate project code now?"):
                                project_dir = _generate_impl(plan_path=str(plan_path))
                                
                                if project_dir:
                                    console.print(f"[bold green]Project ready at: {project_dir}[/bold green]")
                                    
                        except typer.Exit:
                            pass
                        except Exception as e:
                           console.print(f"[red]Error during processing: {e}[/red]")
            
        elif choice == "2":
            # Browse for PDF
            console.print("\n[bold]Where would you like to search?[/bold]")
            console.print("1. Current directory")
            console.print("2. Common locations (Downloads, Documents, Desktop, Home)")
            console.print("3. Browse folders interactively")
            console.print("4. Enter custom path")
            
            location_choice = Prompt.ask("Choose location", choices=["1", "2", "3", "4"])
            
            folder_path = None
            
            if location_choice == "1":
                folder_path = Path.cwd()
                console.print(f"[cyan]Using current directory: {folder_path}[/cyan]")
                
            elif location_choice == "2":
                # Show common locations
                common_locs = get_common_pdf_locations()
                
                if not common_locs:
                    console.print("[red]No common locations found[/red]")
                    continue
                
                table = Table(title="Common PDF Locations")
                table.add_column("#", style="cyan", no_wrap=True)
                table.add_column("Location", style="magenta")
                table.add_column("Path", style="green")
                
                for i, loc in enumerate(common_locs, 1):
                    label = loc.name if loc.name else "Home"
                    if str(loc) == str(Path.cwd()):
                        label = "Current directory"
                    table.add_row(str(i), label, str(loc))
                
                console.print(table)
                
                loc_choice = Prompt.ask("Select location (number)", choices=[str(i) for i in range(1, len(common_locs) + 1)])
                folder_path = common_locs[int(loc_choice) - 1]
                console.print(f"[cyan]Selected: {folder_path}[/cyan]")
                
            elif location_choice == "3":
                # Browse folders interactively
                try:
                    folder_path = select_folder_interactive()
                except KeyboardInterrupt:
                    console.print("[yellow]Cancelled[/yellow]")
                    continue
                    
            elif location_choice == "4":
                # Custom path
                custom_path_str = Prompt.ask("Enter folder path")
                folder_path = Path(custom_path_str).expanduser()
                
                if not folder_path.exists():
                    console.print(f"[red]Path not found: {folder_path}[/red]")
                    continue
                
                if not folder_path.is_dir():
                    console.print(f"[red]Path is not a directory: {folder_path}[/red]")
                    continue
                
                console.print(f"[cyan]Using: {folder_path}[/cyan]")
            
            if not folder_path:
                continue
            
            # Ask about recursive search
            recursive = Confirm.ask("Search subdirectories?", default=False)
            
            # Find PDFs
            try:
                console.print(f"[bold cyan]Searching for PDFs in {folder_path}...[/bold cyan]")
                pdfs = find_pdfs_in_folder(folder_path, recursive=recursive)
            except (FileNotFoundError, NotADirectoryError) as e:
                console.print(f"[red]Error: {e}[/red]")
                continue
            
            if not pdfs:
                console.print(f"[yellow]No PDFs found in {folder_path}[/yellow]")
                if Confirm.ask("Try different location?", default=True):
                    continue
                else:
                    continue
            
            # Show PDFs and let user select
            try:
                selected_pdf = select_pdf_interactive(folder_path, recursive=recursive)
                console.print(f"[green]Selected: {selected_pdf.name}[/green]")
                
                if Confirm.ask("Generate implementation plan for this paper?"):
                    try:
                        # Use internal impl to avoid OptionInfo error
                        plan_path = _plan_impl(paper_id=str(selected_pdf))
                        
                        if plan_path and Confirm.ask(f"\nPlan saved to {plan_path}. Generate project code now?"):
                            project_dir = _generate_impl(plan_path=str(plan_path))
                            
                            if project_dir:
                                console.print(f"[bold green]Project ready at: {project_dir}[/bold green]")
                                
                    except typer.Exit:
                        pass
                    except Exception as e:
                        console.print(f"[red]Error during processing: {e}[/red]")
                        
            except FileNotFoundError as e:
                console.print(f"[red]Error: {e}[/red]")
            except KeyboardInterrupt:
                console.print("[yellow]Cancelled[/yellow]")

@app.command()
def implement(
    task: str = typer.Argument(..., help="Natural language description of what to implement"),
    paper_id: Optional[str] = typer.Option(None, help="arXiv ID if you have a specific paper"),
    max_results: int = typer.Option(3, help="Max papers to search if no paper_id provided"),
    project_name: Optional[str] = typer.Option(None, help="Name for the generated project"),
    output_dir: str = typer.Option("~/mathpilot_projects", help="Base directory for projects"),
    execute: bool = typer.Option(False, help="Execute the generated code after creation"),
):
    """
    End-to-end workflow: search for papers, generate plan, create project, and optionally execute.
    
    This is the main entry point that orchestrates the full implementation workflow.
    """
    from rich.console import Console
    from rich.panel import Panel
    from mathpilot.search import ArxivClient
    from mathpilot.parser import parse_paper
    from mathpilot.planner import generate_plan
    from mathpilot.generator import generate_project_code, generate_requirements
    from mathpilot.workspace import create_project
    from mathpilot.executor import execute_script
    import os
    import tempfile
    from pathlib import Path

    console = Console()
    console.print(Panel.fit(f"[bold cyan]MathPilot Implementation Workflow[/bold cyan]", border_style="blue"))
    
    # Step 1: Find or use provided paper
    paper_title = "Unknown Paper"
    pdf_path = None
    
    if paper_id:
        console.print(f"\n[bold]Step 1: Resolving paper:[/bold] {paper_id}")
        with console.status(f"[bold blue]Fetching paper: {paper_id}..."):
            client = ArxivClient()
            papers = client.search(paper_id)
            if not papers:
                console.print(f"[red]Paper not found: {paper_id}[/red]")
                raise typer.Exit(code=1)
            paper = papers[0]
            paper_title = paper.title
            
            cache_dir = os.path.expanduser("~/.mathpilot/cache")
            os.makedirs(cache_dir, exist_ok=True)
            pdf_path = os.path.join(cache_dir, f"{paper.id}.pdf")
            
            if not os.path.exists(pdf_path):
                console.print(f"Downloading PDF...")
                if paper.pdf_url:
                    client.download_pdf(str(paper.pdf_url), pdf_path)
                else:
                    console.print("[red]No PDF URL found.[/red]")
                    raise typer.Exit(code=1)
            else:
                console.print(f"[dim]Using cached PDF[/dim]")
    else:
        console.print(f"\n[bold]Step 1: Searching papers:[/bold] {task}")
        with console.status(f"[bold green]Searching arXiv..."):
            client = ArxivClient(max_results=max_results)
            papers = client.search(task)
        
        if not papers:
            console.print("[red]No papers found.[/red]")
            raise typer.Exit(code=1)
        
        paper = papers[0]
        paper_title = paper.title
        console.print(f"[green]Found: {paper_title}[/green]")
        
        cache_dir = os.path.expanduser("~/.mathpilot/cache")
        os.makedirs(cache_dir, exist_ok=True)
        pdf_path = os.path.join(cache_dir, f"{paper.id}.pdf")
        
        if not os.path.exists(pdf_path):
            console.print(f"Downloading PDF...")
            if paper.pdf_url:
                with console.status("Downloading..."):
                    client.download_pdf(str(paper.pdf_url), pdf_path)
            else:
                console.print("[red]No PDF URL found.[/red]")
                raise typer.Exit(code=1)
        else:
            console.print(f"[dim]Using cached PDF[/dim]")
    
    # Step 2: Parse PDF
    console.print(f"\n[bold]Step 2: Parsing paper content[/bold]")
    with console.status(f"[bold yellow]Extracting algorithms (this may take 1-2 minutes)..."):
        try:
            parsed_paper = parse_paper(pdf_path, paper_title)
            console.print(f"[green]✓ Extracted {len(parsed_paper.algorithms)} algorithm(s)[/green]")
        except Exception as e:
            console.print(f"[red]Parsing failed: {e}[/red]")
            logger.exception("Parse failed")
            raise typer.Exit(code=1)
    
    if not parsed_paper.algorithms:
        console.print("[red]No algorithms found in paper.[/red]")
        raise typer.Exit(code=1)
    
    algorithm = parsed_paper.algorithms[0]
    
    # Step 3: Generate Plan
    console.print(f"\n[bold]Step 3: Generating implementation plan[/bold]")
    console.print(f"Algorithm: [cyan]{algorithm.name}[/cyan]")
    
    with console.status(f"[bold magenta]Structuring workflow..."):
        try:
            plan_obj = generate_plan(paper_title, algorithm)
            console.print(f"[green]✓ Generated {len(plan_obj.steps)} workflow steps[/green]")
        except Exception as e:
            console.print(f"[red]Planning failed: {e}[/red]")
            logger.exception("Planning failed")
            raise typer.Exit(code=1)
    
    # Step 4: Generate Code
    console.print(f"\n[bold]Step 4: Generating starter code[/bold]")
    with console.status(f"[bold magenta]Creating code templates..."):
        try:
            templates = generate_project_code(plan_obj)
            console.print(f"[green]✓ Generated {len(templates)} code files[/green]")
        except Exception as e:
            console.print(f"[red]Code generation failed: {e}[/red]")
            logger.exception("Code generation failed")
            raise typer.Exit(code=1)
    
    # Step 5: Create Project
    console.print(f"\n[bold]Step 5: Creating project workspace[/bold]")
    
    if not project_name:
        safe_name = "".join(c if c.isalnum() else "_" for c in algorithm.name)
        project_name = safe_name.lower()
    
    with console.status(f"[bold blue]Setting up project..."):
        try:
            project = create_project(
                name=project_name,
                task=plan_obj.summary,
                paper_title=paper_title,
                base_dir=output_dir
            )
            console.print(f"[green]✓ Created at: {project.root_dir}[/green]")
        except Exception as e:
            console.print(f"[red]Project creation failed: {e}[/red]")
            logger.exception("Project creation failed")
            raise typer.Exit(code=1)
    
    # Step 6: Write Files
    console.print(f"\n[bold]Step 6: Writing project files[/bold]")
    with console.status(f"[bold yellow]Writing to disk..."):
        try:
            for filename, template in templates.items():
                file_path = project.code_dir / filename
                with open(file_path, "w") as f:
                    f.write(template.code)
            
            reqs = generate_requirements(templates)
            with open(project.root_dir / "requirements.txt", "w") as f:
                f.write(reqs)
            
            console.print(f"[green]✓ Files written[/green]")
        except Exception as e:
            console.print(f"[red]Failed to write files: {e}[/red]")
            logger.exception("File writing failed")
            raise typer.Exit(code=1)
    
    # Summary
    console.print(f"\n[bold green]✓ Project Ready![/bold green]")
    console.print(f"Location: [cyan]{project.root_dir}[/cyan]")
    console.print(f"\nNext steps:")
    console.print(f"  cd {project.root_dir}")
    console.print(f"  pip install -r requirements.txt")
    console.print(f"  python src/main.py")
    
    # Optional: execute
    if execute and templates:
        console.print(f"\n[bold]Step 7: Executing generated code[/bold]")
        # Find the first generated Python file
        first_file = next((f for f in templates.keys() if f.endswith('.py')), None)
        if first_file:
            script_path = project.code_dir / first_file
            console.print(f"Executing: [cyan]{first_file}[/cyan]")
            
            with console.status("Running..."):
                result = execute_script(str(script_path), timeout=300)
            
            if result.success:
                console.print("[bold green]✓ Execution Successful[/bold green]")
                if result.stdout:
                    console.print("\n[dim]Output:[/dim]")
                    console.print(result.stdout[:500])  # Truncate long output
            else:
                console.print(f"[bold yellow]⚠ Execution exited with code {result.exit_code}[/bold yellow]")
                if result.stderr:
                    console.print("\n[dim]Errors:[/dim]")
                    console.print(result.stderr[:500])
        else:
            console.print("[yellow]No executable files generated[/yellow]")

if __name__ == "__main__":
    app()
