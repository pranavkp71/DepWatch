import asyncio
import re
from typing import Optional

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from app.github import GitHubClient
from app.pypi import PyPIClient
from app.scoring import HealthStatus, ScoringEngine
from app.services import DependencyAnalyzer, DependencyScanner, TransitiveDependencyResolver

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


async def run_scan(repo_url: str, transitive: bool = False, depth: int = 3):
    """Core logic for scanning a repository."""
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

    all_deps = []
    if transitive:
        with console.status("[bold blue]Resolving transitive dependencies...[/bold blue]"):
            pypi_client = PyPIClient()
            resolver = TransitiveDependencyResolver(pypi_client, max_depth=depth)
            all_deps = await resolver.resolve(dependencies)
        console.print(
            f"📦 Found [bold]{len(dependencies)}[/bold] direct and "
            f"[bold]{len(all_deps) - len(dependencies)}[/bold] transitive dependencies."
        )
    else:
        # Wrap direct deps into DependencyNode-like structure for the loop
        from app.services import DependencyNode
        all_deps = [DependencyNode(name=d) for d in dependencies]
        console.print(f"📦 Found [bold]{len(all_deps)}[/bold] dependencies. Analyzing health...")

    reviews = []
    counts = {
        HealthStatus.RISKY: 0,
        HealthStatus.WARNING: 0,
        HealthStatus.HEALTHY: 0,
        HealthStatus.UNKNOWN: 0,
    }

    # Analyze in batches or sequentially for MVP
    for node in all_deps:
        dep_name = node.name
        with console.status(f"Analyzing {dep_name}..."):
            try:
                signals = await analyzer.analyze(dep_name)
                review = engine.classify(signals)
                counts[review.status] += 1
                reviews.append((node, review))
            except Exception as e:
                counts[HealthStatus.UNKNOWN] += 1
                from app.scoring.engine import HealthReview

                unknown = HealthReview(
                    status=HealthStatus.UNKNOWN,
                    signals=[str(e)],
                )
                reviews.append((node, unknown))

    console.print()
    if counts[HealthStatus.RISKY] > 0:
        risky = counts[HealthStatus.RISKY]
        console.print(f"⚠️  [bold red]{risky}[/bold red] risky")
    if counts[HealthStatus.WARNING] > 0:
        console.print(f"🟡 [bold yellow]{counts[HealthStatus.WARNING]}[/bold yellow] warnings")
    if counts[HealthStatus.HEALTHY] > 0:
        console.print(f"🟢 [bold green]{counts[HealthStatus.HEALTHY]}[/bold green] healthy")
    if counts[HealthStatus.UNKNOWN] > 0:
        console.print(f"⚪ [bold white]{counts[HealthStatus.UNKNOWN]}[/bold white] unknown")
    console.print()

    for node, review in reviews:
        dep_name = node.name
        color = "green"
        if review.status == HealthStatus.RISKY:
            color = "red"
        elif review.status == HealthStatus.WARNING:
            color = "yellow"
        elif review.status == HealthStatus.UNKNOWN:
            color = "white"

        conf_map = {"High": "green", "Medium": "yellow"}
        conf_color = conf_map.get(review.confidence, "red")

        # Build signals list
        signal_text = Text()
        for s in review.signals:
            signal_text.append(f"  • {s}\n", style="dim")

        role = "direct" if node.is_direct else "transitive"
        role_style = "bold blue" if node.is_direct else "bold magenta"

        panel_items = [
            Text.assemble(("Status: ", "bold"), (f"{review.status.value}", f"bold {color}")),
            Text.assemble(("Type: ", "bold"), (f"[{role}]", role_style)),
            Text.assemble(("Risk Score: ", "bold"), (f"{review.risk_score}/10", "cyan")),
            Text.assemble(("Confidence: ", "bold"), (f"{review.confidence}", conf_color)),
        ]

        # Add dependency path for transitive deps if not healthy
        if not node.is_direct:
            panel_items.append(Text.assemble(("\nPath: ", "bold"), (node.dependency_path, "dim italic")))

        panel_items.extend([
            Text("\nSignals:", style="bold"),
            signal_text,
            Text.assemble(
                ("Action: ", "bold"),
                (
                    f"{review.recommendation}",
                    "italic yellow"
                    if review.status != HealthStatus.HEALTHY
                    else "dim green",
                ),
            ),
        ])

        panel_content = Group(*panel_items)

        console.print(Panel(
            panel_content,
            title=f"[bold]{dep_name}[/bold]",
            border_style=color,
            expand=False,
        ))
        console.print()


@app.command(name="scan")
def scan_command(
    repo_url: str = typer.Argument(..., help="GitHub repository URL to scan"),
    transitive: bool = typer.Option(False, "--transitive", "-t", help="Analyze transitive dependencies"),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum depth for transitive analysis"),
) -> None:
    """Scan a GitHub repository and report dependency health."""
    asyncio.run(run_scan(repo_url, transitive=transitive, depth=depth))


@app.command(name="version")
def version_command() -> None:
    """Show the current depwatch version."""
    console.print("depwatch [bold cyan]v0.1.0[/bold cyan]")


def main():
    """Entry point for the depwatch script."""
    app()


if __name__ == "__main__":
    main()
