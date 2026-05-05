from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from app.github import GitHubClient
from app.scoring import HealthStatus, ScoringEngine
from app.services import DependencyAnalyzer, DependencyScanner

app = FastAPI(
    title="DepWatch",
    description="Dependency Health Scanner — Are your dependencies risky right now?",
    version="0.1.0",
)


class ScanRequest(BaseModel):
    repo_url: HttpUrl


class DependencyReport(BaseModel):
    name: str
    status: HealthStatus
    risk_score: int
    confidence: str
    signals: List[str]
    recommendation: str
    repo_url: Optional[str] = None


class ScanResponse(BaseModel):
    owner: str
    repo: str
    dependencies: list[DependencyReport]


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/scan", response_model=ScanResponse)
async def scan_repository(request: ScanRequest):
    """Scan a repository and return health report."""
    from cli.main import parse_github_url

    owner, repo = parse_github_url(str(request.repo_url))
    if not owner or not repo:
        raise HTTPException(
            status_code=400, detail="Invalid GitHub URL. Expected: https://github.com/owner/repo"
        )

    client = GitHubClient()
    scanner = DependencyScanner(client)
    analyzer = DependencyAnalyzer(client)
    engine = ScoringEngine()

    try:
        dependencies = await scanner.extract_dependencies(owner, repo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dependencies: {e}")

    reports = []
    for dep_name in dependencies:
        try:
            signals = await analyzer.analyze(dep_name)
            review = engine.classify(signals)
            reports.append(
                DependencyReport(
                    name=dep_name,
                    status=review.status,
                    risk_score=review.risk_score,
                    confidence=review.confidence,
                    signals=review.signals,
                    recommendation=review.recommendation,
                    repo_url=signals.repo_url
                )
            )
        except Exception:
            reports.append(
                DependencyReport(
                    name=dep_name, 
                    status=HealthStatus.UNKNOWN, 
                    risk_score=0,
                    confidence="Low",
                    signals=["Analysis failed"],
                    recommendation="Retry later"
                )
            )

    return ScanResponse(owner=owner, repo=repo, dependencies=reports)
