"""
War Room Benchmark — Bar Chart Visualisation
Axes: Test Case × Scoring Category × Before/After
One subplot per scoring category, TC-001..TC-005 on x-axis, before/after bars.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

DIMS = ["Argument Quality", "Reasoning Diversity", "Engagement Quality",
        "Conflict Resolution", "Discussion Utility"]

after_rows = [
    ("TC-001", "Healthy tech",         7.0, 6.3, 7.0, 4.7, 5.3),
    ("TC-002", "Struggling retail",    7.3, 6.0, 7.0, 4.7, 5.7),
    ("TC-003", "Ambiguous fintech",    7.7, 6.7, 7.7, 5.7, 7.0),
    ("TC-004", "Semiconductor",        7.5, 7.0, 7.3, 5.3, 6.3),
    ("TC-005", "Regional bank",        8.0, 6.7, 7.7, 5.7, 6.0),
]

before_rows = [
    ("TC-001", "Healthy tech",         4.7, 1.3, 2.3, 0.7, 1.0),
    ("TC-002", "Struggling retail",    4.3, 1.7, 2.0, 1.0, 1.3),
    ("TC-003", "Ambiguous fintech",    3.7, 1.3, 2.3, 0.7, 1.0),
    ("TC-004", "Semiconductor",        4.0, 1.7, 2.0, 0.7, 1.3),
    ("TC-005", "Regional bank",        4.3, 1.3, 2.7, 1.0, 1.0),
]

cols = ["test_case", "description"] + DIMS
df_after  = pd.DataFrame(after_rows,  columns=cols)
df_before = pd.DataFrame(before_rows, columns=cols)

tc_labels = df_after["test_case"].tolist()
x = np.arange(len(tc_labels))
width = 0.35

COLOR_BEFORE = "#E07B54"
COLOR_AFTER  = "#4CAF82"

out_dir = os.path.dirname(os.path.abspath(__file__))

# ── Figure 1: One subplot per scoring category ─────────────────────────────
fig, axes = plt.subplots(1, len(DIMS), figsize=(22, 5), sharey=True)
fig.suptitle(
    "War Room Discussion Quality — Before vs After\n"
    "(Average across Gemini 3 · GPT-4o mini · Claude Sonnet 4.6)",
    fontsize=13, fontweight="bold"
)

for ax, dim in zip(axes, DIMS):
    b_vals = df_before[dim].values
    a_vals = df_after[dim].values

    bars_b = ax.bar(x - width / 2, b_vals, width, label="Before",
                    color=COLOR_BEFORE, edgecolor="white", linewidth=0.6)
    bars_a = ax.bar(x + width / 2, a_vals, width, label="After",
                    color=COLOR_AFTER,  edgecolor="white", linewidth=0.6)

    # Value labels
    for bar in bars_b:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.15,
                f"{h:.1f}", ha="center", va="bottom", fontsize=7.5, color="#555")
    for bar in bars_a:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.15,
                f"{h:.1f}", ha="center", va="bottom", fontsize=7.5, color="#222")

    ax.set_title(dim, fontsize=10, fontweight="bold", pad=6)
    ax.set_xticks(x)
    ax.set_xticklabels(tc_labels, fontsize=8.5, rotation=30, ha="right")
    ax.set_ylim(0, 11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

axes[0].set_ylabel("Score (0 – 10)", fontsize=10)

legend_handles = [
    mpatches.Patch(color=COLOR_BEFORE, label="Before"),
    mpatches.Patch(color=COLOR_AFTER,  label="After"),
]
fig.legend(handles=legend_handles, loc="lower center", ncol=2,
           fontsize=10, frameon=False, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout(rect=[0, 0.04, 1, 1])
path1 = os.path.join(out_dir, "warroom_barchart_by_category.png")
plt.savefig(path1, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {path1}")

# ── Figure 2: One subplot per test case ────────────────────────────────────
fig2, axes2 = plt.subplots(1, len(tc_labels), figsize=(22, 5), sharey=True)
fig2.suptitle(
    "War Room Discussion Quality — Before vs After (per Test Case)\n"
    "(Average across Gemini 3 · GPT-4o mini · Claude Sonnet 4.6)",
    fontsize=13, fontweight="bold"
)

x2 = np.arange(len(DIMS))
short_dims = ["Arg.\nQuality", "Reasoning\nDiversity", "Engagement", "Conflict\nResol.", "Utility"]

for ax, (_, row_b), (_, row_a) in zip(axes2, df_before.iterrows(), df_after.iterrows()):
    b_vals = [row_b[d] for d in DIMS]
    a_vals = [row_a[d] for d in DIMS]

    bars_b = ax.bar(x2 - width / 2, b_vals, width, color=COLOR_BEFORE,
                    edgecolor="white", linewidth=0.6)
    bars_a = ax.bar(x2 + width / 2, a_vals, width, color=COLOR_AFTER,
                    edgecolor="white", linewidth=0.6)

    for bar in bars_b:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.15,
                f"{h:.1f}", ha="center", va="bottom", fontsize=7, color="#555")
    for bar in bars_a:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.15,
                f"{h:.1f}", ha="center", va="bottom", fontsize=7, color="#222")

    tc = row_a["test_case"]
    desc = row_a["description"]
    ax.set_title(f"{tc}\n{desc}", fontsize=8.5, fontweight="bold", pad=6)
    ax.set_xticks(x2)
    ax.set_xticklabels(short_dims, fontsize=7.5, rotation=30, ha="right")
    ax.set_ylim(0, 11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

axes2[0].set_ylabel("Score (0 – 10)", fontsize=10)

fig2.legend(handles=legend_handles, loc="lower center", ncol=2,
            fontsize=10, frameon=False, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout(rect=[0, 0.04, 1, 1])
path2 = os.path.join(out_dir, "warroom_barchart_by_testcase.png")
plt.savefig(path2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {path2}")
