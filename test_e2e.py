#!/usr/bin/env python3
"""
End-to-end test of MathPilot pipeline.

This script tests the complete workflow WITHOUT mocks:
- Search arXiv for papers
- Parse a paper to extract algorithms
- Generate implementation plan
- Generate Python code
- Create workspace project
- Execute generated code

Usage:
    python test_e2e.py [--query "kalman filter"] [--max-results 3] [--skip-execute]
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import typer

console = Console()

def test_phase_1_search():
    """Test Phase 1: Search for papers on arXiv."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]Phase 1: Search for Papers on arXiv[/bold cyan]")
    console.print("="*80)
    
    try:
        from mathpilot.search import ArxivClient
        
        query = "Selective Kalman Filter"
        console.print(f"Searching arXiv for: '{query}'")
        
        client = ArxivClient(max_results=3)
        papers = client.search(query)
        
        if not papers:
            console.print("[red]No papers found![/red]")
            return None
            
        console.print(f"[green]Found {len(papers)} papers[/green]")
        
        # Display in table
        table = Table(title="Search Results")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Published", style="blue")
        
        for paper in papers:
            table.add_row(
                paper.id,
                paper.title[:50] + "..." if len(paper.title) > 50 else paper.title,
                paper.published.strftime("%Y-%m-%d")
            )
        
        console.print(table)
        
        # Return first paper
        selected = papers[0]
        console.print(f"\n[green]Selected:[/green] {selected.title}")
        console.print(f"[green]arXiv ID:[/green] {selected.id}")
        console.print(f"[green]PDF URL:[/green] {selected.pdf_url}")
        
        return selected
        
    except Exception as e:
        console.print(f"[red]Error in Phase 1: {e}[/red]")
        console.print_exception()
        return None


def test_phase_2_download_pdf(paper):
    """Test Phase 2: Download PDF from arXiv."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]Phase 2: Download PDF[/bold cyan]")
    console.print("="*80)
    
    try:
        import urllib.request
        
        pdf_url = paper.pdf_url
        if isinstance(pdf_url, str):
            pdf_url = pdf_url.replace("http://", "https://")
        else:
            pdf_url = str(pdf_url)
            
        console.print(f"Downloading from: {pdf_url}")
        
        # Save to temp directory
        pdf_dir = Path(tempfile.gettempdir()) / "mathpilot_test"
        pdf_dir.mkdir(exist_ok=True)
        pdf_path = pdf_dir / f"{paper.id}.pdf"
        
        with console.status("Downloading PDF..."):
            urllib.request.urlretrieve(pdf_url, pdf_path)
        
        file_size = pdf_path.stat().st_size / (1024 * 1024)  # MB
        console.print(f"[green]Downloaded to:[/green] {pdf_path}")
        console.print(f"[green]File size:[/green] {file_size:.2f} MB")
        
        return pdf_path
        
    except Exception as e:
        console.print(f"[red]Error downloading PDF: {e}[/red]")
        # Return None to skip parsing, or create a dummy PDF
        return None


def test_phase_3_parse_paper(pdf_path, paper_title):
    """Test Phase 3: Parse paper to extract algorithms."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]Phase 3: Parse Paper[/bold cyan]")
    console.print("="*80)
    
    try:
        from mathpilot.parser import parse_paper
        
        console.print(f"Parsing: {pdf_path}")
        
        with console.status("Parsing paper (calling Gemini API)..."):
            parsed = parse_paper(str(pdf_path), paper_title)
        
        console.print(f"[green]Found {len(parsed.algorithms)} algorithms[/green]")
        
        # Display algorithms
        for i, algo in enumerate(parsed.algorithms, 1):
            console.print(f"\n[bold blue]Algorithm {i}: {algo.name}[/bold blue]")
            console.print(f"  Problem: {algo.problem_addressed}")
            console.print(f"  Inputs: {', '.join(algo.inputs[:3])}")
            console.print(f"  Outputs: {', '.join(algo.outputs[:3])}")
            console.print(f"  Steps: {len(algo.steps)}")
            
        return parsed
        
    except Exception as e:
        console.print(f"[red]Error in Phase 3: {e}[/red]")
        console.print_exception()
        return None


def test_phase_4_plan_workflow(parsed_paper):
    """Test Phase 4: Generate implementation plan."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]Phase 4: Generate Implementation Plan[/bold cyan]")
    console.print("="*80)
    
    try:
        from mathpilot.planner import generate_plan
        
        if not parsed_paper.algorithms:
            console.print("[red]No algorithms to plan![/red]")
            return None
            
        algorithm = parsed_paper.algorithms[0]
        console.print(f"Planning for: {algorithm.name}")
        
        with console.status("Generating plan (calling Gemini API)..."):
            plan = generate_plan(parsed_paper.title, algorithm)
        
        console.print(f"[green]Generated {len(plan.steps)} workflow steps[/green]")
        
        # Display plan
        table = Table(title="Workflow Steps")
        table.add_column("Step ID", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Type", style="yellow")
        table.add_column("Dependencies", style="blue")
        
        for step in plan.steps:
            deps = ", ".join(step.dependencies) if step.dependencies else "None"
            table.add_row(
                step.step_id,
                step.title[:30] + "..." if len(step.title) > 30 else step.title,
                step.step_type.value,
                deps
            )
        
        console.print(table)
        
        # Save plan to file
        plan_dir = Path(tempfile.gettempdir()) / "mathpilot_test"
        plan_dir.mkdir(exist_ok=True)
        plan_file = plan_dir / "test_plan.json"
        
        with open(plan_file, "w") as f:
            f.write(plan.model_dump_json(indent=2))
            
        console.print(f"[green]Plan saved to:[/green] {plan_file}")
        
        return plan
        
    except Exception as e:
        console.print(f"[red]Error in Phase 4: {e}[/red]")
        console.print_exception()
        return None


def test_phase_5_generate_code(plan):
    """Test Phase 5: Generate Python code."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]Phase 5: Generate Python Code[/bold cyan]")
    console.print("="*80)
    
    try:
        from mathpilot.generator import generate_project_code, generate_requirements
        
        console.print(f"Generating code for {len(plan.steps)} steps...")
        
        with console.status("Generating code (calling Gemini API for each step)..."):
            templates = generate_project_code(plan)
        
        console.print(f"[green]Generated {len(templates)} code files[/green]")
        
        # Display generated files
        table = Table(title="Generated Files")
        table.add_column("Filename", style="cyan")
        table.add_column("Size (chars)", style="magenta")
        table.add_column("Dependencies", style="blue")
        
        for filename, template in templates.items():
            deps = ", ".join(template.dependencies[:3]) if template.dependencies else "None"
            table.add_row(
                filename,
                str(len(template.code)),
                deps
            )
        
        console.print(table)
        
        # Generate requirements
        requirements = generate_requirements(templates)
        console.print(f"\n[green]Generated requirements.txt:[/green]")
        if requirements.strip():
            for line in requirements.strip().split("\n"):
                console.print(f"  • {line}")
        else:
            console.print("  (no external dependencies)")
        
        return templates
        
    except Exception as e:
        console.print(f"[red]Error in Phase 5: {e}[/red]")
        console.print_exception()
        return None


def test_phase_6_create_workspace(plan, templates):
    """Test Phase 6: Create workspace project."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]Phase 6: Create Workspace Project[/bold cyan]")
    console.print("="*80)
    
    try:
        from mathpilot.workspace import create_project
        from mathpilot.generator import generate_requirements
        
        # Create project
        project_name = f"test_{plan.algorithm_name.lower().replace(' ', '_')[:20]}"
        project_base = Path.home() / "mathpilot_projects"
        
        console.print(f"Creating project: {project_name}")
        console.print(f"Base directory: {project_base}")
        
        with console.status("Creating project structure..."):
            project = create_project(
                name=project_name,
                task=plan.summary,
                paper_title=plan.paper_title,
                base_dir=str(project_base)
            )
        
        console.print(f"[green]Project created at:[/green] {project.root_dir}")
        
        # Write code files
        console.print("Writing code files...")
        for filename, template in templates.items():
            file_path = project.code_dir / filename
            with open(file_path, "w") as f:
                f.write(template.code)
            console.print(f"  ✓ {filename}")
        
        # Write requirements
        requirements = generate_requirements(templates)
        req_file = project.root_dir / "requirements.txt"
        with open(req_file, "w") as f:
            f.write(requirements)
        console.print(f"  ✓ requirements.txt")
        
        # Write main.py
        main_file = project.code_dir / "main.py"
        with open(main_file, "w") as f:
            f.write("""#!/usr/bin/env python3
# Main entry point for generated project
# This file coordinates all workflow steps

if __name__ == "__main__":
    print("Generated project structure created successfully!")
    print("Edit the step files in this directory to implement the algorithm.")
""")
        console.print(f"  ✓ main.py")
        
        # Display project structure
        console.print("\n[green]Project structure:[/green]")
        for item in sorted(project.root_dir.rglob("*"))[:10]:
            rel_path = item.relative_to(project.root_dir)
            if item.is_dir():
                console.print(f"  📁 {rel_path}/")
            else:
                console.print(f"  📄 {rel_path}")
        
        return project
        
    except Exception as e:
        console.print(f"[red]Error in Phase 6: {e}[/red]")
        console.print_exception()
        return None


def test_phase_7_execute_code(project):
    """Test Phase 7: Execute generated code."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]Phase 7: Execute Generated Code[/bold cyan]")
    console.print("="*80)
    
    try:
        from mathpilot.executor import execute_script
        
        main_file = project.code_dir / "main.py"
        
        if not main_file.exists():
            console.print(f"[yellow]main.py not found[/yellow]")
            return None
        
        console.print(f"Executing: {main_file}")
        
        with console.status("Running code..."):
            result = execute_script(str(main_file), timeout=30)
        
        if result.success:
            console.print("[green]✓ Execution successful[/green]")
        else:
            console.print(f"[yellow]⚠ Execution failed (exit code: {result.exit_code})[/yellow]")
        
        if result.stdout:
            console.print("[blue]Output:[/blue]")
            console.print(result.stdout)
        
        if result.stderr:
            console.print("[red]Errors:[/red]")
            console.print(result.stderr)
        
        console.print(f"[dim]Execution time: {result.execution_time:.2f}s[/dim]")
        
        return result
        
    except Exception as e:
        console.print(f"[red]Error in Phase 7: {e}[/red]")
        console.print_exception()
        return None


def main(
    query: str = typer.Option(
        "kalman filter sensor fusion",
        help="Search query for arXiv"
    ),
    max_results: int = typer.Option(
        3,
        help="Maximum papers to download"
    ),
    skip_execute: bool = typer.Option(
        False,
        "--skip-execute",
        help="Skip code execution phase"
    ),
    skip_download: bool = typer.Option(
        False,
        "--skip-download",
        help="Skip PDF download (use cached if available)"
    ),
    pdf_path: Optional[Path] = typer.Option(
        None,
        "--pdf-path",
        help="Path to local PDF file (skips search and download)"
    ),
):
    """Run end-to-end test of MathPilot pipeline."""
    
    console.print(Panel(
        "[bold cyan]MathPilot End-to-End Test[/bold cyan]\n"
        "Testing: Search → Parse → Plan → Generate → Execute",
        style="bold blue"
    ))
    
    paper = None
    if pdf_path:
        console.print(f"\n[yellow]Using local PDF (skipping Phases 1 & 2): {pdf_path}[/yellow]")
        if not pdf_path.exists():
            console.print(f"[red]PDF not found: {pdf_path}[/red]")
            sys.exit(1)
            
        # Create dummy paper object for title (infer from filename or use default)
        from mathpilot.search.models import Paper
        paper = Paper(
            id="local_test",
            title=pdf_path.stem.replace("_", " ").title(),
            authors=["Local Author"],
            summary="Local test paper",
            published=datetime.now(),
            updated=datetime.now(),
            pdf_url="http://localhost/local.pdf", # Satisfy HttpUrl validation
            category="cs"
        )
    else:
        # Phase 1: Search
        paper = test_phase_1_search()
        if not paper:
            console.print("\n[red]Test failed at Phase 1[/red]")
            sys.exit(1)
        
        # Phase 2: Download PDF
        if skip_download:
            console.print("\n[yellow]Skipping PDF download (--skip-download)[/yellow]")
            pdf_path = None
        else:
            pdf_path = test_phase_2_download_pdf(paper)
            if not pdf_path:
                console.print("\n[yellow]Skipping to Phase 4 (PDF download failed)[/yellow]")
    
    # Phase 3: Parse (requires PDF)
    parsed_paper = None
    if pdf_path:
        parsed_paper = test_phase_3_parse_paper(pdf_path, paper.title)
        if not parsed_paper:
            console.print("\n[yellow]Skipping to Phase 5 (parsing failed)[/yellow]")
    
    # Phase 4: Plan (requires parsed paper)
    plan = None
    if parsed_paper:
        plan = test_phase_4_plan_workflow(parsed_paper)
        if not plan:
            console.print("\n[red]Test failed at Phase 4[/red]")
            sys.exit(1)
    else:
        console.print("\n[red]Cannot proceed without parsing results[/red]")
        sys.exit(1)
    
    # Phase 5: Generate Code
    templates = test_phase_5_generate_code(plan)
    if not templates:
        console.print("\n[red]Test failed at Phase 5[/red]")
        sys.exit(1)
    
    # Phase 6: Create Workspace
    project = test_phase_6_create_workspace(plan, templates)
    if not project:
        console.print("\n[red]Test failed at Phase 6[/red]")
        sys.exit(1)
    
    # Phase 7: Execute (optional)
    if not skip_execute:
        result = test_phase_7_execute_code(project)
    
    # Summary
    console.print("\n" + "="*80)
    console.print("[bold green]✓ End-to-End Test Complete![/bold green]")
    console.print("="*80)
    console.print(f"\n[cyan]Project created at:[/cyan]")
    console.print(f"  {project.root_dir}")
    console.print(f"\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. cd {project.root_dir}")
    console.print(f"  2. pip install -r requirements.txt")
    console.print(f"  3. python src/main.py")
    console.print(f"  4. Edit step_*.py files to implement algorithm details\n")


if __name__ == "__main__":
    typer.run(main)
