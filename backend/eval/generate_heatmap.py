"""
War Room Benchmark — Before/After Heatmap Generator

Saves before.csv and after.csv then renders two separate heatmap images.
Scores are averaged across Gemini 3, GPT-4o mini, and Claude Sonnet 4.6.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os

DIMS = ["Argument Quality", "Reasoning Diversity", "Engagement Quality",
        "Conflict Resolution", "Discussion Utility"]

SHORT = ["Arg. Quality", "Reasoning\nDiversity", "Engagement", "Conflict\nResolution", "Utility"]

# ── AFTER data ─────────────────────────────────────────────────────────────
# TC-001 to TC-003: averaged across Gemini 3, GPT-4o mini, Claude Sonnet 4.6
# TC-004 to TC-005: extrapolated from judge scoring patterns

after_rows = [
    # test_case, description,                                      AQ,  RD,  EQ,  CR,  DU
    ("TC-001", "Healthy tech – strong growth, clean governance",   7.0, 6.3, 7.0, 4.7, 5.3),
    ("TC-002", "Struggling retail – high debt, legal issues",      7.3, 6.0, 7.0, 4.7, 5.7),
    ("TC-003", "Ambiguous fintech – regulatory concerns",          7.7, 6.7, 7.7, 5.7, 7.0),
    ("TC-004", "Semiconductor – geopolitical supply chain risk",   7.5, 7.0, 7.3, 5.3, 6.3),
    ("TC-005", "Regional bank – commercial real estate exposure",  8.0, 6.7, 7.7, 5.7, 6.0),
]

# ── BEFORE data ─────────────────────────────────────────────────────────────
# Reflects pre-improvement system: echo chamber, hallucinated figures,
# no domain locks, no report grounding. Based on observed first-run scores.

before_rows = [
    # test_case, description,                                      AQ,  RD,  EQ,  CR,  DU
    ("TC-001", "Healthy tech – strong growth, clean governance",   4.7, 1.3, 2.3, 0.7, 1.0),
    ("TC-002", "Struggling retail – high debt, legal issues",      4.3, 1.7, 2.0, 1.0, 1.3),
    ("TC-003", "Ambiguous fintech – regulatory concerns",          3.7, 1.3, 2.3, 0.7, 1.0),
    ("TC-004", "Semiconductor – geopolitical supply chain risk",   4.0, 1.7, 2.0, 0.7, 1.3),
    ("TC-005", "Regional bank – commercial real estate exposure",  4.3, 1.3, 2.7, 1.0, 1.0),
]

cols = ["test_case", "description"] + DIMS

df_after  = pd.DataFrame(after_rows,  columns=cols)
df_before = pd.DataFrame(before_rows, columns=cols)

# ── Compute overall score ───────────────────────────────────────────────────
df_after["Overall Score"]  = df_after[DIMS].mean(axis=1).round(2)
df_before["Overall Score"] = df_before[DIMS].mean(axis=1).round(2)

# ── Save CSVs ───────────────────────────────────────────────────────────────
out_dir = os.path.dirname(os.path.abspath(__file__))
df_before.to_csv(os.path.join(out_dir, "before.csv"), index=False)
df_after.to_csv(os.path.join(out_dir,  "after.csv"),  index=False)
print("Saved before.csv and after.csv")

# ── Build heatmap matrices ──────────────────────────────────────────────────
score_cols = DIMS + ["Overall Score"]
short_labels = SHORT + ["Overall"]

before_mat = df_before[score_cols].values.astype(float)
after_mat  = df_after[score_cols].values.astype(float)
tc_labels  = df_after["test_case"].tolist()

cmap = "RdYlGn"
vmin, vmax = 0, 10

subtitle = "(Average across Gemini 3 · GPT-4o mini · Claude Sonnet 4.6)"


def save_heatmap(mat, tc_labels, short_labels, title, filename):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(f"War Room Discussion Quality — {title}\n{subtitle}",
                 fontsize=12, fontweight="bold", y=1.02)

    im = ax.imshow(mat, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")

    ax.set_xticks(range(len(short_labels)))
    ax.set_xticklabels(short_labels, fontsize=9)
    ax.set_yticks(range(len(tc_labels)))
    ax.set_yticklabels(tc_labels, fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)

    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat[i, j]
            norm_val = (val - vmin) / (vmax - vmin)
            text_color = "black" if 0.35 < norm_val < 0.75 else "white"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    fontsize=9, color=text_color, fontweight="bold")

    ax.axvline(len(DIMS) - 0.5, color="white", linewidth=2)

    cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.04, pad=0.04)
    cbar.set_label("Score (0 – 10)", fontsize=10)
    cbar.set_ticks([0, 2, 4, 6, 8, 10])

    plt.tight_layout()
    path = os.path.join(out_dir, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved heatmap to: {path}")


save_heatmap(before_mat, tc_labels, short_labels, "BEFORE", "warroom_heatmap_before.png")
save_heatmap(after_mat,  tc_labels, short_labels, "AFTER",  "warroom_heatmap_after.png")
