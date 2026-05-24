# naijarec_cold-start Application

This directory contains the containerized Task B submission application. It accepts a natural-language user persona and returns personalized restaurant or grocery product recommendations. It also packages the evaluated MPG/hybrid ranking outputs for Yelp and Amazon Grocery so judges can view the models associated with the reported results.

For the offline model reproduction pipeline, dataset preparation, retrieval/reranking commands, and reported metrics, see the project [reproducibility README](../README.md).

## Application Files

```text
app/
  Dockerfile
  Dockerfile.dockerignore
  README.md
  requirements.txt
  main.py
  naijarec_cold_start.py
  benchmark.py
  recommender.py
  model_artifacts/
  static/
```

`naijarec_cold_start.py` uses underscores because Python module names cannot contain the hyphen in the displayed project name `naijarec_cold-start`.

## Supported Recommendations

| Domain value | Output | Optional location filter |
| --- | --- | --- |
| `restaurants` | Nigerian-contextualized Yelp restaurant recommendations | `Philadelphia`, `Tampa`, `Nashville` |
| `amazon_grocery` | Full Amazon Grocery product recommendations | None |
| `amazon_grocery_dense` | Dense Amazon Grocery product recommendations | None |

The application contains two modes:

| Interface mode | Input | Model behavior |
| --- | --- | --- |
| `New Persona` | New free-text persona | Cold-start semantic profile matching over the selected Yelp or Amazon metadata catalog |
| `Evaluated Model` | Held-out evaluation user and model method | Packaged rankings produced by the evaluated MPG or MPG + Gemini hybrid experiment |

The evaluated artifacts correspond to:

| Evaluated dataset | Packaged methods | Reported headline result |
| --- | --- | --- |
| Yelp cold-start user-disjoint test set | MPG, hybrid `alpha=0.3`, hybrid `alpha=0.6` | Best `NDCG@20 = 0.620736` |
| Amazon Grocery full catalog | MPG with enriched `full_text` | `NDCG@20 = 0.320753` |
| Amazon Grocery dense true 3-core | MPG, Gemini hybrid `alpha=0.6` | Best `NDCG@20 = 0.488582` |

The distinction matters: a completely new persona cannot be looked up in an offline held-out user ranking. New personas therefore use the online cold-start semantic scorer; packaged benchmark users expose the exact evaluated model outputs. Gemini is not called at runtime, so judges can run the image without an API key or API quota dependency.

## Gemini API Key Policy

Do **not** place a Gemini API key in this application image, JavaScript, source control, or the submitted `.env` file. Gemini was used during the offline hybrid-reranking experiment; the resulting evaluated rankings are already exported into `app/model_artifacts/` and served in `Evaluated Model` mode.

An API key is only required when rerunning the offline Gemini reranker before artifact export. This is described in the repository-level reproduction instructions, and the key should be supplied locally through an environment variable rather than committed to the repository.

The browser deliberately reports the runtime architecture accurately:

| Mode | Runtime retriever | Runtime reranker |
| --- | --- | --- |
| `New Persona` | Metadata profile matching over the selected catalog | None |
| `Evaluated Model` | Packaged MPG output | Packaged hybrid output when the selected method includes Gemini hybrid reranking |

## Packaged Evaluated Model Artifacts

The image includes these compact deployment artifacts through `COPY app ./app` in `app/Dockerfile`:

```text
app/model_artifacts/yelp_cold_start.json
app/model_artifacts/amazon_grocery_full.json
app/model_artifacts/amazon_grocery_dense.json
```

They store test-user keyword evidence and ranked item IDs resolved from the saved MPG/hybrid outputs. To recreate them after rerunning the offline models:

```bash
python taskB/export_app_model_artifacts.py
```

The export uses:

```text
data/out2LLMs/*_q20_knn2rest.json
data/reviews/*.csv
reRanker/results_rerank/...json
```

## Required Metadata Files

The Docker image packages these item-profile files from the repository-level `data/metadata/` directory. They are excluded from GitHub because of their size. Upload the files to Google Drive, enable **Anyone with the link: Viewer**, and replace the placeholder links before submission.

| Required repository path | Approx. size | Google Drive link |
| --- | ---: | --- |
| `data/metadata/naija_yelp_paper_restaurant_detail.csv` | 3.5 MB | `<ADD_GOOGLE_DRIVE_LINK_NAIJA_METADATA>` |
| `data/metadata/amazonGrocery_restaurant_detail.csv` | 80 MB | `<ADD_GOOGLE_DRIVE_LINK_AMAZON_FULL_METADATA>` |
| `data/metadata/amazonGrocery_dense_restaurant_detail.csv` | 7.3 MB | `<ADD_GOOGLE_DRIVE_LINK_AMAZON_DENSE_METADATA>` |

Download them before building:

```bash
mkdir -p data/metadata
python -m pip install gdown

python -m gdown --fuzzy "<ADD_GOOGLE_DRIVE_LINK_NAIJA_METADATA>" \
  -O data/metadata/naija_yelp_paper_restaurant_detail.csv
python -m gdown --fuzzy "<ADD_GOOGLE_DRIVE_LINK_AMAZON_FULL_METADATA>" \
  -O data/metadata/amazonGrocery_restaurant_detail.csv
python -m gdown --fuzzy "<ADD_GOOGLE_DRIVE_LINK_AMAZON_DENSE_METADATA>" \
  -O data/metadata/amazonGrocery_dense_restaurant_detail.csv
```

## Run With Docker

Run the following commands from the repository root. The Dockerfile lives in `app/`, while the root build context makes `data/metadata/` available to package in the image.

```bash
docker build -f app/Dockerfile -t naijarec_cold-start .
docker run --rm -p 8001:8001 naijarec_cold-start
```

On machines where Docker access requires administrator privileges, run the same commands as:

```bash
sudo docker build -f app/Dockerfile -t naijarec_cold-start .
sudo docker run --rm -p 8001:8001 naijarec_cold-start
```

Open the web interface:

```text
http://localhost:8001/
```

Open interactive API documentation:

```text
http://localhost:8001/docs
```

## Run Locally

Run from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.naijarec_cold_start:app --host 0.0.0.0 --port 8001
```

## Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Browser application |
| `GET /health` | Runtime health and metadata availability |
| `GET /datasets` | Supported domain configuration |
| `POST /recommend` | Generate persona-based recommendations |
| `GET /benchmark/models` | Packaged evaluated models, methods, metrics and sample user IDs |
| `GET /benchmark/users/{model}` | Available held-out evaluation users for a packaged model |
| `POST /benchmark/recommend` | Display packaged MPG/hybrid recommendations for an evaluation user |
| `GET /docs` | OpenAPI interface |

In the browser, restaurant and grocery sample personas are kept aligned with the selected domain. Live persona result cards display location, categories, rating/price when available, a `Matched signals` summary, and a readable recommendation explanation. Evaluated rankings display their reported metrics and held-out keyword evidence.

### Restaurant Request

```bash
curl -X POST http://localhost:8001/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "restaurants",
    "top_k": 5,
    "city": "Philadelphia",
    "persona": "A Nigerian student in Philadelphia who likes spicy jollof, halal meat, generous portions, affordable food, and warm service for group dinners."
  }'
```

### Grocery Request

```bash
curl -X POST http://localhost:8001/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "amazon_grocery_dense",
    "top_k": 5,
    "persona": "A health-conscious shopper who likes organic gluten-free snacks, spicy sauces, coffee, tea, and affordable pantry staples."
  }'
```

### Evaluated Yelp Hybrid Model Request

```bash
curl -X POST http://localhost:8001/benchmark/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "model": "yelp_cold_start",
    "method": "hybrid_alpha_0.3",
    "top_k": 10
  }'
```

### Evaluated Dense Amazon Hybrid Model Request

```bash
curl -X POST http://localhost:8001/benchmark/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "model": "amazon_grocery_dense",
    "method": "hybrid_alpha_0.6",
    "top_k": 10
  }'
```

## Request Schema

```json
{
  "persona": "natural-language user persona",
  "domain": "restaurants | amazon_grocery | amazon_grocery_dense",
  "top_k": 5,
  "city": "optional city for restaurant recommendations"
}
```

## Submission Verification

Before uploading:

1. Replace each Google Drive placeholder with a viewer-accessible public URL.
2. Ensure no `.env` file or API key is included in the repository or image.
3. Ensure the three files in `app/model_artifacts/` exist, or recreate them with `python taskB/export_app_model_artifacts.py`.
4. Build the image from a clean checkout after restoring the three metadata files.
5. Open `http://localhost:8001/` and test both `New Persona` and `Evaluated Model` modes.
6. Verify API behavior with `POST /recommend` and `POST /benchmark/recommend`.
