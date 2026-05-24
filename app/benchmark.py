import json
from pathlib import Path


class BenchmarkModelService:
    """Serve exported rankings from the evaluated MPG and hybrid runs."""

    def __init__(self, recommendation_service, root_dir="."):
        self.recommendation_service = recommendation_service
        root = Path(root_dir)
        self.artifact_dir = root / "app/model_artifacts"
        self.artifact_paths = {
            "yelp_cold_start": self.artifact_dir / "yelp_cold_start.json",
            "amazon_grocery_full": self.artifact_dir / "amazon_grocery_full.json",
            "amazon_grocery_dense": self.artifact_dir / "amazon_grocery_dense.json",
        }
        self.cache = {}

    def models(self):
        output = {}
        for model_key in self.artifact_paths:
            model = self._model(model_key)
            output[model_key] = {
                "label": model["label"],
                "domain": model["domain"],
                "default_method": model["default_method"],
                "methods": model["methods"],
                "test_users": len(model["users"]),
                "sample_user_id": next(iter(model["users"])),
            }
        return output

    def users(self, model_key, limit=30):
        model = self._model(model_key)
        limit = max(1, min(int(limit), 100))
        return [
            {"user_id": user_id, "keywords": user["keywords"][:8]}
            for user_id, user in list(model["users"].items())[:limit]
        ]

    def recommend(self, model_key, user_id=None, method=None, top_k=10):
        model = self._model(model_key)
        if user_id is None:
            user_id = next(iter(model["users"]))
        if user_id not in model["users"]:
            raise KeyError(f"Evaluation user '{user_id}' does not exist in model '{model_key}'.")
        method = method or model["default_method"]
        if method not in model["methods"]:
            raise KeyError(f"Method '{method}' does not exist in model '{model_key}'.")

        top_k = max(1, min(int(top_k), 20))
        user = model["users"][user_id]
        item_ids = user["rankings"][method][:top_k]
        profile_index = self.recommendation_service.profile_index(model["domain"])
        method_label = model["methods"][method]["label"]
        evidence = ", ".join(user["keywords"][:8])
        reason = f"{method_label} ranking from held-out user keyword evidence: {evidence}"

        return {
            "mode": "evaluated_model",
            "model": model_key,
            "model_label": model["label"],
            "method": method,
            "method_label": method_label,
            "user_id": user_id,
            "keywords": user["keywords"],
            "reported_metrics": model["methods"][method]["reported_metrics"],
            "top_k": top_k,
            "count": len(item_ids),
            "recommendations": [
                profile_index.ranked_item(item_id, rank, reason)
                for rank, item_id in enumerate(item_ids, start=1)
            ],
        }

    def _model(self, model_key):
        if model_key not in self.artifact_paths:
            raise KeyError(f"Unknown evaluated model '{model_key}'. Available models: {', '.join(self.artifact_paths)}")
        if model_key not in self.cache:
            path = self.artifact_paths[model_key]
            if not path.is_file():
                raise KeyError(f"Packaged model artifact not found: {path}")
            with path.open(encoding="utf-8") as file:
                self.cache[model_key] = json.load(file)
        return self.cache[model_key]
