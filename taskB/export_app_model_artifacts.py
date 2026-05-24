"""Package evaluated model rankings for the containerized application."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "app" / "model_artifacts"

CONFIGS = {
    "yelp_cold_start": {
        "label": "Yelp Restaurants - Cold-Start Test Users",
        "domain": "restaurants",
        "reviews": "data/reviews/naija_yelp_paper.csv",
        "candidates": "data/out2LLMs/naija_yelp_paper_q20_knn2rest.json",
        "methods": {
            "mpg": {
                "label": "MPG Retrieval",
                "kind": "candidate",
                "reported_metrics": {
                    "ndcg@10": 0.619777,
                    "ndcg@20": 0.611271,
                    "hitrate@10": 0.859667,
                    "hitrate@20": 0.913721,
                },
            },
            "hybrid_alpha_0.3": {
                "label": "MPG + Gemini Hybrid (alpha=0.3)",
                "kind": "integer_ranking",
                "path": "reRanker/results_rerank/naija_yelp_paper/hybrid_alpha_0.3_top20.json",
                "reported_metrics": {
                    "ndcg@10": 0.629689,
                    "ndcg@20": 0.620736,
                    "hitrate@10": 0.843035,
                    "hitrate@20": 0.913721,
                },
            },
            "hybrid_alpha_0.6": {
                "label": "MPG + Gemini Hybrid (alpha=0.6)",
                "kind": "integer_ranking",
                "path": "reRanker/results_rerank/naija_yelp_paper/hybrid_alpha_0.6_top20.json",
                "reported_metrics": {
                    "ndcg@10": 0.628581,
                    "ndcg@20": 0.620657,
                    "hitrate@10": 0.860707,
                    "hitrate@20": 0.913721,
                },
            },
        },
        "default_method": "hybrid_alpha_0.3",
    },
    "amazon_grocery_full": {
        "label": "Amazon Grocery - Full Catalog Test Users",
        "domain": "amazon_grocery",
        "reviews": "data/reviews/amazonGrocery.csv",
        "candidates": "data/out2LLMs/amazonGrocery_q20_knn2rest.json",
        "methods": {
            "mpg": {
                "label": "MPG Retrieval with full_text",
                "kind": "candidate",
                "reported_metrics": {
                    "precision@20": 0.035729,
                    "recall@20": 0.099116,
                    "f1@20": 0.050132,
                    "ndcg@20": 0.320753,
                },
            },
        },
        "default_method": "mpg",
    },
    "amazon_grocery_dense": {
        "label": "Amazon Grocery - Dense 3-Core Test Users",
        "domain": "amazon_grocery_dense",
        "reviews": "data/reviews/amazonGrocery_dense.csv",
        "candidates": "data/out2LLMs/amazonGrocery_dense_q20_knn2rest.json",
        "methods": {
            "mpg": {
                "label": "MPG Retrieval",
                "kind": "candidate",
                "reported_metrics": {
                    "precision@20": 0.066827,
                    "recall@20": 0.174981,
                    "f1@20": 0.089956,
                    "ndcg@20": 0.445954,
                },
            },
            "hybrid_alpha_0.6": {
                "label": "MPG + Gemini Hybrid (alpha=0.6)",
                "kind": "integer_ranking",
                "path": "reRanker/results_rerank/amazonGrocery_dense/zeroshot_scored_3_5_pool50_top20_hybrid_alpha_0.6_preserve_12.json",
                "reported_metrics": {
                    "precision@20": 0.066827,
                    "recall@20": 0.174981,
                    "f1@20": 0.089956,
                    "ndcg@20": 0.488582,
                },
            },
        },
        "default_method": "hybrid_alpha_0.6",
    },
}


def read_json(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8") as file:
        return json.load(file)


def build_integer_item_map(relative_path):
    item_to_int = {}
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            item_id = row["rest_id"]
            if item_id not in item_to_int:
                item_to_int[item_id] = len(item_to_int)
    return {str(value): key for key, value in item_to_int.items()}


def package_model(model_key, config):
    candidates = read_json(config["candidates"])
    integer_to_item = build_integer_item_map(config["reviews"])
    integer_rankings = {
        method_key: read_json(method_config["path"])
        for method_key, method_config in config["methods"].items()
        if method_config["kind"] == "integer_ranking"
    }
    users = {}
    for user_id, user_data in candidates.items():
        output = {
            "keywords": user_data.get("kw", [])[:20],
            "rankings": {},
        }
        for method_key, method_config in config["methods"].items():
            if method_config["kind"] == "candidate":
                ranking = user_data.get("candidate", [])[:20]
            else:
                ranking = [
                    integer_to_item[str(item)]
                    for item in integer_rankings[method_key].get(user_id, [])[:20]
                    if str(item) in integer_to_item
                ]
            output["rankings"][method_key] = ranking
        users[user_id] = output

    return {
        "model_key": model_key,
        "label": config["label"],
        "domain": config["domain"],
        "default_method": config["default_method"],
        "methods": {
            key: {
                "label": value["label"],
                "reported_metrics": value["reported_metrics"],
            }
            for key, value in config["methods"].items()
        },
        "users": users,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for model_key, config in CONFIGS.items():
        output = package_model(model_key, config)
        output_path = OUTPUT_DIR / f"{model_key}.json"
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(output, file, separators=(",", ":"))
        print(f"Wrote {output_path.relative_to(ROOT)} ({len(output['users']):,} evaluation users)")


if __name__ == "__main__":
    main()
