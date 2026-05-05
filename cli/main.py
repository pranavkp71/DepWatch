"""Typer CLI entry point for DepWatch."""

import typer

app = typer.Typer(
    name="depwatch",
    help="Dependency Health Scanner — check if your dependencies are risky.",
    add_completion=False,
)


@app.command()
def scan(repo_url: str = typer.Argument(..., help="GitHub repository URL to scan")) -> None:
    """Scan a GitHub repository and report dependency health."""
    typer.echo(f"Scanning {repo_url} ...")
    # TODO: wire up scanner pipeline
    typer.echo("Scanner not yet implemented — coming next!")


if __name__ == "__main__":
    app()
