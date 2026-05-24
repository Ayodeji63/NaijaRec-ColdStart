"""Generate reproducible figures for reported naijarec_cold-start results."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


COLORS = ["#146C94", "#19A7CE", "#F29F05", "#D9485F", "#5B4B8A"]
TEXT = "#18212B"
GRID = "#D9E1E8"


def style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=TEXT)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig, out_dir, filename):
    fig.tight_layout()
    fig.savefig(out_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / f"{filename}.svg", bbox_inches="tight")
    plt.close(fig)


def grouped_bars(ax, labels, metrics, values, colors=None):
    x = np.arange(len(labels))
    width = 0.8 / len(metrics)
    palette = colors or COLORS
    for index, metric in enumerate(metrics):
        positions = x - 0.4 + width / 2 + index * width
        ax.bar(
            positions,
            values[index],
            width,
            label=metric,
            color=palette[index],
        )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)


def yelp_method_comparison(out_dir):
    methods = ["Random", "Popularity", "MPG", "Hybrid\nalpha=0.3", "Hybrid\nalpha=0.6"]
    metrics = ["NDCG@10", "NDCG@20", "HitRate@10", "HitRate@20"]
    values = [
        [0.004646, 0.088333, 0.619777, 0.629689, 0.628581],
        [0.005746, 0.100273, 0.611271, 0.620736, 0.620657],
        [0.035343, 0.374220, 0.859667, 0.843035, 0.860707],
        [0.068607, 0.489605, 0.913721, 0.913721, 0.913721],
    ]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    grouped_bars(ax, methods, metrics, values)
    style_axis(ax)
    ax.set_title(
        "Yelp Cold-Start Model Comparison\nUser-disjoint evaluation, 962 test users",
        fontsize=15,
        weight="bold",
        color=TEXT,
    )
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.02)
    ax.legend(ncol=4, loc="upper left", frameon=False)
    save(fig, out_dir, "yelp_model_comparison")


def amazon_cross_domain_comparison(out_dir):
    methods = [
        "Full catalog\nreview-only",
        "Full catalog\nfull_text",
        "Dense 3-core\nMPG",
        "Dense 3-core\nGemini hybrid",
    ]
    metrics = ["Precision@20", "Recall@20", "F1@20", "NDCG@20"]
    values = [
        [0.007963, 0.035729, 0.066827, 0.066827],
        [0.022153, 0.099116, 0.174981, 0.174981],
        [0.011220, 0.050132, 0.089956, 0.089956],
        [0.070276, 0.320753, 0.445954, 0.488582],
    ]

    fig, ax = plt.subplots(figsize=(11, 6))
    grouped_bars(ax, methods, metrics, values)
    style_axis(ax)
    ax.set_title("Amazon Grocery Cross-Domain Results", fontsize=15, weight="bold", color=TEXT)
    ax.set_ylabel("Score")
    ax.set_ylim(0, 0.56)
    ax.legend(ncol=4, loc="upper left", frameon=False)
    ax.annotate(
        "Metadata enrichment\nraises NDCG@20",
        xy=(1, 0.320753),
        xytext=(0.3, 0.44),
        arrowprops={"arrowstyle": "->", "color": "#52616B"},
        fontsize=9,
        color=TEXT,
    )
    save(fig, out_dir, "amazon_cross_domain_comparison")


def yelp_quantity_ablation(out_dir):
    quantities = ["20 keywords", "50 keywords"]
    metrics = ["Precision@20", "Recall@20", "F1@20", "NDCG@20"]
    values = [
        [0.145166, 0.136746],
        [0.326992, 0.290734],
        [0.184961, 0.170722],
        [0.611271, 0.550238],
    ]

    fig, ax = plt.subplots(figsize=(8.2, 5.3))
    grouped_bars(ax, quantities, metrics, values)
    style_axis(ax)
    ax.set_title("Yelp Keyword Quantity Ablation", fontsize=15, weight="bold", color=TEXT)
    ax.set_ylabel("Score")
    ax.set_ylim(0, 0.68)
    ax.legend(ncol=2, loc="upper right", frameon=False)
    ax.text(
        0.03,
        0.93,
        "quantity=20 retained for final model",
        transform=ax.transAxes,
        fontsize=9,
        color="#52616B",
    )
    save(fig, out_dir, "yelp_quantity_ablation")


def dense_amazon_metric_profile(out_dir):
    cutoffs = [1, 3, 5, 10, 15, 20]
    series = {
        "Precision": [0.355769, 0.216346, 0.161538, 0.107212, 0.080449, 0.066827],
        "Recall": [0.052718, 0.096065, 0.114097, 0.148208, 0.163904, 0.174981],
        "F1": [0.090262, 0.128117, 0.126767, 0.116805, 0.100705, 0.089956],
        "NDCG": [0.355769, 0.437658, 0.461568, 0.483787, 0.483049, 0.488582],
    }

    fig, ax = plt.subplots(figsize=(9.2, 5.5))
    for (label, scores), color in zip(series.items(), COLORS):
        ax.plot(cutoffs, scores, marker="o", linewidth=2.4, color=color, label=label)
    style_axis(ax)
    ax.set_title("Dense Amazon Gemini Hybrid Metrics by Cutoff", fontsize=15, weight="bold", color=TEXT)
    ax.set_xlabel("Recommendation cutoff K")
    ax.set_ylabel("Score")
    ax.set_xticks(cutoffs)
    ax.set_ylim(0, 0.54)
    ax.legend(loc="center right", frameon=False)
    ax.annotate(
        "NDCG@20 = 0.4886",
        xy=(20, 0.488582),
        xytext=(11.5, 0.52),
        arrowprops={"arrowstyle": "->", "color": "#52616B"},
        color=TEXT,
        fontsize=9,
    )
    save(fig, out_dir, "dense_amazon_hybrid_by_cutoff")


def ndcg20_summary(out_dir):
    methods = [
        "Yelp\nPopularity",
        "Yelp\nMPG",
        "Yelp\nHybrid",
        "Amazon full\nreview-only",
        "Amazon full\nfull_text",
        "Amazon dense\nMPG",
        "Amazon dense\nHybrid",
    ]
    ndcg = [0.100273, 0.611271, 0.620736, 0.070276, 0.320753, 0.445954, 0.488582]
    colors = ["#8EA9B8", "#146C94", "#19A7CE", "#D4A373", "#F29F05", "#D9485F", "#5B4B8A"]

    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    bars = ax.bar(methods, ndcg, color=colors, width=0.68)
    style_axis(ax)
    ax.set_title("NDCG@20 Summary Across Evaluated Settings", fontsize=15, weight="bold", color=TEXT)
    ax.set_ylabel("NDCG@20")
    ax.set_ylim(0, 0.69)
    for bar, score in zip(bars, ndcg):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            score + 0.012,
            f"{score:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=TEXT,
        )
    save(fig, out_dir, "ndcg20_summary")


def main():
    parser = argparse.ArgumentParser(description="Plot recorded naijarec_cold-start experiment results.")
    parser.add_argument("--out_dir", default="docs/figures", help="Directory for PNG and SVG chart outputs.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelcolor": TEXT,
            "axes.titlepad": 15,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    yelp_method_comparison(out_dir)
    amazon_cross_domain_comparison(out_dir)
    yelp_quantity_ablation(out_dir)
    dense_amazon_metric_profile(out_dir)
    ndcg20_summary(out_dir)
    print(f"Wrote result charts to {out_dir}")


if __name__ == "__main__":
    main()
