"""
File browser utilities for interactive folder and PDF selection.

Provides functions for:
- Finding PDFs in folders (with recursive option)
- Listing common PDF locations (Downloads, Documents, Desktop, Home)
- Interactive folder browsing
- Interactive PDF selection with rich tables
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table


def get_common_pdf_locations() -> List[Path]:
    """
    Return list of common PDF locations that exist on the system.
    
    Checks (in order): Downloads, Documents, Desktop, Home, Current directory
    Only returns paths that exist (graceful degradation).
    
    Returns:
        List[Path]: Existing common locations, sorted by likelihood
        
    Example:
        >>> locations = get_common_pdf_locations()
        >>> len(locations) > 0
        True
    """
    home = Path.home()
    candidates = [
        home / "Downloads",
        home / "Documents",
        home / "Desktop",
        home,
        Path.cwd(),
    ]
    
    existing = []
    for path in candidates:
        if path.exists() and path.is_dir():
            # Avoid duplicates
            if path not in existing:
                existing.append(path)
    
    return existing


def find_pdfs_in_folder(folder: Path, recursive: bool = False) -> List[Path]:
    """
    Find all PDF files in a folder (optionally recursive).
    
    Args:
        folder: Path to folder to search
        recursive: If True, search subdirectories too (depth-first)
    
    Returns:
        List[Path]: All found PDFs, sorted by modification time (newest first)
        
    Raises:
        FileNotFoundError: If folder doesn't exist
        NotADirectoryError: If path is not a directory
        
    Example:
        >>> from pathlib import Path
        >>> pdfs = find_pdfs_in_folder(Path.home() / "Downloads", recursive=True)
        >>> all(p.suffix == ".pdf" for p in pdfs)
        True
    """
    folder = Path(folder)
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder}")  # Check dir before file
    
    pdfs = []
    
    try:
        if recursive:
            # Search all subdirectories recursively
            pdfs = list(folder.rglob("*.pdf"))
        else:
            # Search only immediate directory
            pdfs = list(folder.glob("*.pdf"))
    except PermissionError:
        # Graceful degradation for permission errors
        pass
    
    # Sort by modification time (newest first)
    pdfs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return pdfs


def list_directories(path: Path) -> List[Path]:
    """
    List immediate subdirectories in a path.
    
    Args:
        path: Path to search
    
    Returns:
        List[Path]: Subdirectories (excluding hidden ones starting with .)
                   Sorted alphabetically
                   
    Raises:
        FileNotFoundError: If path doesn't exist
        NotADirectoryError: If path is not a directory
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    try:
        dirs = [
            p for p in path.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ]
        dirs.sort(key=lambda p: p.name)
        return dirs
    except PermissionError:
        return []


def select_folder_interactive(start_path: Optional[Path] = None) -> Path:
    """
    Interactive folder browser using rich UI.
    
    Shows:
    - Current directory path
    - Numbered list of subdirectories
    - Option to go to parent directory (..)
    - Option to enter custom path
    
    Args:
        start_path: Starting folder (defaults to Home)
    
    Returns:
        Path: Selected folder path
        
    Example:
        >>> folder = select_folder_interactive()
        >>> folder.exists()
        True
    """
    console = Console()
    
    current = start_path or Path.home()
    
    while True:
        try:
            console.print(f"\n[bold cyan]Current directory:[/bold cyan] {current}")
            
            # List subdirectories
            dirs = list_directories(current)
            
            if dirs:
                console.print("[bold]Subdirectories:[/bold]")
                for i, d in enumerate(dirs, 1):
                    console.print(f"  {i}. {d.name}")
            else:
                console.print("[dim]No subdirectories found.[/dim]")
            
            # Build choices
            choices = [str(i) for i in range(1, len(dirs) + 1)]
            
            # Add parent option if not at root
            if current.parent != current:  # Not at filesystem root
                console.print(f"  {len(dirs) + 1}. [dim].. (Parent directory)[/dim]")
                choices.append(str(len(dirs) + 1))
            
            console.print(f"  [bold cyan]C[/bold cyan]. [cyan]Enter custom path[/cyan]")
            console.print(f"  [bold green]U[/bold green]. [green]Use this directory[/green]")
            
            choice = Prompt.ask("Select option", choices=choices + ["C", "U", "c", "u"])
            
            if choice.upper() == "U":
                return current
            elif choice.upper() == "C":
                custom_path = Prompt.ask("Enter path")
                custom = Path(custom_path).expanduser()
                if custom.exists() and custom.is_dir():
                    current = custom
                else:
                    console.print(f"[red]Invalid path: {custom}[/red]")
            else:
                idx = int(choice) - 1
                # Check if it's parent option
                if current.parent != current and idx == len(dirs):
                    current = current.parent
                elif 0 <= idx < len(dirs):
                    current = dirs[idx]
                else:
                    console.print("[red]Invalid selection[/red]")
        
        except (ValueError, KeyError):
            console.print("[red]Invalid input[/red]")
        except FileNotFoundError:
            console.print("[red]Directory not found[/red]")
            current = Path.home()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def select_pdf_interactive(folder: Path, recursive: bool = False) -> Path:
    """
    Display PDFs in folder as rich table, let user select one.
    
    Shows table with columns:
    - Number (1, 2, 3, ...)
    - Filename (basename only)
    - Size (human-readable: 2.5 MB, 890 KB, etc)
    - Modified date (YYYY-MM-DD HH:MM:SS)
    
    Args:
        folder: Path to folder
        recursive: If True, search subfolders too
    
    Returns:
        Path: Full path to selected PDF
        
    Raises:
        FileNotFoundError: If no PDFs found
        
    Example:
        >>> from pathlib import Path
        >>> pdf = select_pdf_interactive(Path.home() / "Downloads")
        >>> pdf.suffix
        '.pdf'
    """
    console = Console()
    folder = Path(folder)
    
    # Find PDFs
    pdfs = find_pdfs_in_folder(folder, recursive=recursive)
    
    if not pdfs:
        raise FileNotFoundError(f"No PDFs found in {folder}")
    
    # Create table
    table = Table(title=f"PDFs in {folder}")
    table.add_column("#", style="cyan", no_wrap=True)
    table.add_column("Filename", style="magenta")
    table.add_column("Size", style="green")
    table.add_column("Modified", style="blue")
    
    for i, pdf in enumerate(pdfs, 1):
        try:
            size_bytes = pdf.stat().st_size
            size_str = _format_size(size_bytes)
            
            mtime = datetime.fromtimestamp(pdf.stat().st_mtime)
            date_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
        except OSError:
            size_str = "?"
            date_str = "?"
        
        table.add_row(str(i), pdf.name, size_str, date_str)
    
    console.print(table)
    
    # Let user select
    choices = [str(i) for i in range(1, len(pdfs) + 1)]
    selection = Prompt.ask("Select PDF (number)", choices=choices)
    
    idx = int(selection) - 1
    return pdfs[idx]


def _format_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable size string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size (e.g., "2.5 MB", "890 KB", "1.2 GB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            if unit == "B":
                return f"{size_bytes:.0f} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"
