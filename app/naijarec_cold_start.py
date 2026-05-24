from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.benchmark import BenchmarkModelService
from app.recommender import RecommendationService


app = FastAPI(
    title="naijarec_cold-start API",
    description="Containerized Task B API: user persona in, personalized recommendations out.",
    version="1.0.0",
)
service = RecommendationService()
benchmark_service = BenchmarkModelService(service)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


class RecommendRequest(BaseModel):
    persona: str = Field(
        ...,
        min_length=5,
        description="Natural-language user persona or current recommendation context.",
        examples=[
            "A Nigerian student in Philadelphia who likes spicy jollof, halal meat, generous portions, and affordable places for group dinners."
        ],
    )
    domain: str = Field(
        "restaurants",
        description="Recommendation domain: restaurants, amazon_grocery, or amazon_grocery_dense.",
    )
    top_k: int = Field(10, ge=1, le=50, description="Number of recommendations to return.")
    city: Optional[str] = Field(
        None,
        description="Optional city filter for restaurant recommendations, e.g. Philadelphia, Tampa, Nashville.",
    )


class RecommendationResponse(BaseModel):
    domain: str
    top_k: int
    count: int
    recommendations: list[dict]


class BenchmarkRequest(BaseModel):
    model: str = Field("yelp_cold_start", description="Packaged evaluated model.")
    method: Optional[str] = Field(None, description="Ranking method inside the selected evaluated model.")
    user_id: Optional[str] = Field(None, description="Held-out evaluation user; omit to use the sample user.")
    top_k: int = Field(10, ge=1, le=20, description="Number of ranked items to return.")


@app.get("/health")
def health():
    return {"status": "ok", "app": "naijarec_cold-start", "datasets": service.datasets()}


@app.get("/")
def root():
    return FileResponse("app/static/index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return {}


@app.get("/datasets")
def datasets():
    return service.datasets()


@app.get("/benchmark/models")
def benchmark_models():
    try:
        return benchmark_service.models()
    except KeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/benchmark/users/{model}")
def benchmark_users(model: str, limit: int = 30):
    try:
        return benchmark_service.users(model, limit)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(payload: RecommendRequest):
    try:
        recommendations = service.recommend(
            persona=payload.persona,
            domain=payload.domain,
            top_k=payload.top_k,
            city_filter=payload.city,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "domain": payload.domain,
        "top_k": payload.top_k,
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@app.post("/benchmark/recommend")
def benchmark_recommend(payload: BenchmarkRequest):
    try:
        return benchmark_service.recommend(
            model_key=payload.model,
            method=payload.method,
            user_id=payload.user_id,
            top_k=payload.top_k,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
