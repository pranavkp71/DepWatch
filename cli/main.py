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
        console.print("[red] Invalid GitHub URL.[/red] Expected: https://github.com/owner/repo")
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
            console.print(f"[red] Error fetching dependencies:[/red] {e}")
            raise typer.Exit(1)

    if not dependencies:
        console.print(
            "[yellow]⚠️ No dependencies found (package.json or requirements.txt missing).[/yellow]"
        )
        return

    console.print(f"📦 Found [bold]{len(dependencies)}[/bold] dependencies. Analyzing health...")

    results = []
    counts = {HealthStatus.RISKY: 0, HealthStatus.WARNING: 0, HealthStatus.HEALTHY: 0, HealthStatus.UNKNOWN: 0}

    # Analyze in batches or sequentially for MVP
    for dep_name in dependencies:
        with console.status(f"Analyzing {dep_name}..."):
            try:
                signals = await analyzer.analyze(dep_name)
                status, reason, confidence = engine.classify(signals)
                counts[status] += 1
                results.append((dep_name, status, reason, confidence))
            except Exception as e:
                counts[HealthStatus.UNKNOWN] += 1
                results.append((dep_name, HealthStatus.UNKNOWN, str(e), "Low"))

    console.print()
    if counts[HealthStatus.RISKY] > 0:
        console.print(f"⚠️  [bold red]{counts[HealthStatus.RISKY]}[/bold red] risky dependencies found")
    if counts[HealthStatus.WARNING] > 0:
        console.print(f"🟡 [bold yellow]{counts[HealthStatus.WARNING]}[/bold yellow] warnings")
    if counts[HealthStatus.HEALTHY] > 0:
        console.print(f"🟢 [bold green]{counts[HealthStatus.HEALTHY]}[/bold green] healthy")
    if counts[HealthStatus.UNKNOWN] > 0:
        console.print(f"⚪ [bold white]{counts[HealthStatus.UNKNOWN]}[/bold white] unknown")
    console.print()

    table = Table(title=f"Health Report for {owner}/{repo}")
    table.add_column("Dependency", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Reason", style="dim")
    table.add_column("Confidence", justify="center")

    for dep_name, status, reason, confidence in results:
        emoji = "🟢"
        if status == HealthStatus.RISKY:
            emoji = "🔴"
        elif status == HealthStatus.WARNING:
            emoji = "🟡"
        elif status == HealthStatus.UNKNOWN:
            emoji = "⚪"
            
        conf_color = "green" if confidence == "High" else ("yellow" if confidence == "Medium" else "red")
        table.add_row(dep_name, f"{emoji} {status.value}", reason, f"[{conf_color}]{confidence}[/{conf_color}]")

    console.print(table)


@app.command(name="scan")
def scan_command(repo_url: str = typer.Argument(..., help="GitHub repository URL to scan")) -> None:
    """Scan a GitHub repository and report dependency health."""
    asyncio.run(run_scan(repo_url))


@app.command(name="version")
def version_command() -> None:
    """Show the current depwatch version."""
    console.print("depwatch [bold cyan]v0.1.0[/bold cyan]")


def main():
    """Entry point for the depwatch script."""
    app()


if __name__ == "__main__":
    main()
