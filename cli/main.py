import asyncio
import re
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.github import GitHubClient
from app.scoring import HealthStatus, ScoringEngine
from app.services import DependencyAnalyzer, DependencyScanner

app = typer.Typer(
    name="depwatch",
    help="Dependency Health Scanner — check if your dependencies are risky.",
    add_completion=False,
)

console = Console()


def parse_github_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """Extract owner and repo from a GitHub URL."""
    # Pattern to match github.com/owner/repo
    pattern = r"github\.com/([^/]+)/([^/]+?)(?:\.git|/)?$"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None


async def run_scan(repo_url: str):
    """Core logic for scanning a repository."""
    owner, repo = parse_github_url(repo_url)
    if not owner or not repo:
        console.print("[red]❌ Invalid GitHub URL.[/red] Expected: https://github.com/owner/repo")
        raise typer.Exit(1)

    # Use a environment variable for token if available
    client = GitHubClient()
    scanner = DependencyScanner(client)
    analyzer = DependencyAnalyzer(client)
    engine = ScoringEngine()

    with console.status(f"[bold blue]Scanning {owner}/{repo}...[/bold blue]"):
        try:
            dependencies = await scanner.extract_dependencies(owner, repo)
        except Exception as e:
            console.print(f"[red]❌ Error fetching dependencies:[/red] {e}")
            raise typer.Exit(1)

    if not dependencies:
        console.print(
            "[yellow]⚠️ No dependencies found (package.json or requirements.txt missing).[/yellow]"
        )
        return

    console.print(f"📦 Found [bold]{len(dependencies)}[/bold] dependencies. Analyzing health...")

    table = Table(title=f"Health Report for {owner}/{repo}")
    table.add_column("Dependency", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Reason", style="dim")

    # Analyze in batches or sequentially for MVP
    for dep_name in dependencies:
        with console.status(f"Analyzing {dep_name}..."):
            try:
                signals = await analyzer.analyze(dep_name)
                status, reason = engine.classify(signals)

                emoji = "🟢"
                if status == HealthStatus.RISKY:
                    emoji = "🔴"
                elif status == HealthStatus.WARNING:
                    emoji = "🟡"
                elif status == HealthStatus.UNKNOWN:
                    emoji = "⚪"

                table.add_row(dep_name, f"{emoji} {status.value}", reason)
            except Exception as e:
                table.add_row(dep_name, "⚪ Error", str(e))

    console.print(table)


@app.command()
def scan(repo_url: str = typer.Argument(..., help="GitHub repository URL to scan")) -> None:
    """Scan a GitHub repository and report dependency health."""
    asyncio.run(run_scan(repo_url))


if __name__ == "__main__":
    app()
