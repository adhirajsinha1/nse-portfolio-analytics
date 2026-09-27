"""
Shared chart style so every figure in the project looks consistent.

Usage in a notebook:
    import sys; sys.path.append("../src")
    from chart_style import apply_style, COLORS, save
    apply_style()
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Colour-blind-safe categorical palette, used in this fixed order (never shuffled)
COLORS = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "violet": "#4a3aa7",
    "grey": "#898781",      # for context / de-emphasised data
}
PALETTE = [COLORS[c] for c in ["blue", "orange", "aqua", "yellow", "magenta", "violet"]]

FIG_DIR = Path(__file__).resolve().parent.parent / "reports" / "figures"


def apply_style():
    """Clean look: no box around the chart, light grid, readable text."""
    plt.rcParams.update({
        "figure.figsize": (10, 4.5),
        "figure.dpi": 110,
        "figure.facecolor": "#fcfcfb",
        "axes.facecolor": "#fcfcfb",
        "axes.edgecolor": "#898781",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,          # grid lines behind the bars, not on top
        "grid.color": "#e6e5e0",
        "grid.linewidth": 0.8,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelcolor": "#52514e",
        "xtick.color": "#52514e",
        "ytick.color": "#52514e",
        "lines.linewidth": 2,
        "axes.prop_cycle": plt.cycler(color=PALETTE),
        "legend.frameon": False,
    })


def pct_axis(ax, axis="y", decimals=0):
    """Format an axis as percentages (input values are fractions, e.g. 0.12 -> 12%)."""
    fmt = mticker.PercentFormatter(xmax=1, decimals=decimals)
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def money_axis(ax, axis="y", unit="k"):
    """Format an axis as ₹120k / ₹1.2M instead of 120000."""
    div, suffix = (1e3, "k") if unit == "k" else (1e6, "M")
    fmt = mticker.FuncFormatter(lambda x, _: f"₹{x/div:,.0f}{suffix}" if unit == "k" else f"₹{x/div:,.1f}{suffix}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def save(fig, name):
    """Save a figure to reports/figures/<name>.png (used in the README)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight", dpi=150)
