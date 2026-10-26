#!/usr/bin/env python3
"""Draw figures from provided SWMM summary numbers; this does not rerun SWMM."""

from __future__ import annotations

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Figures"
METRICS = ROOT / "results" / "scenario_metrics.json"
RAINFALL = ROOT / "Data" / "Minneapolis_NOAA14_10yr24h_Q1_50pct_15min.dat"

NAVY, TEAL, GREEN, AMBER = "#19354d", "#168a8a", "#32986c", "#c88933"
GRAY, GRID = "#697b89", "#e3e9ed"
ORDER = ("Baseline", "Green_S1", "Green_All")
LABELS = ("Baseline", "S1 gardens", "All-six gardens")
COLORS = (GRAY, TEAL, GREEN)


def style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
        "font.size": 12,
        "axes.edgecolor": GRID,
        "axes.labelcolor": NAVY,
        "text.color": NAVY,
        "xtick.color": NAVY,
        "ytick.color": NAVY,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.facecolor": "white",
    })


def grid(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, pad=7)


def save(fig, name):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    fig.savefig(path, dpi=220, facecolor="white", bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print(f"Saved {path}")


def plot_scenarios(data):
    sc = data["scenarios"]
    defs = [
        ("Surface runoff", "acre-ft", lambda s: sc[s]["runoff_acft"], False),
        ("Total infiltration", "acre-ft", lambda s: sc[s]["infiltration_acft"], True),
        ("C3 peak discharge", "CFS", lambda s: sc[s]["links"]["C3"]["peak_flow_cfs"], False),
        ("C3 maximum velocity", "ft/s", lambda s: sc[s]["links"]["C3"]["max_velocity_fts"], False),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.2), layout="constrained")
    fig.suptitle("Stormwater response to distributed rain gardens", fontsize=23, weight="bold")
    for ax, (title, unit, getter, higher_is_better) in zip(axes.flat, defs):
        vals = [getter(name) for name in ORDER]
        bars = ax.bar(range(3), vals, color=COLORS, width=0.60)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, v + max(vals)*0.022,
                    f"{v:.2f}", ha="center", fontsize=12.5, weight="bold")
        pct = (vals[-1] / vals[0] - 1) * 100
        better = (pct > 0) == higher_is_better
        ax.text(0.98, 0.96, f"{abs(pct):.1f}% {'increase' if pct>0 else 'reduction'}",
                transform=ax.transAxes, ha="right", va="top", fontsize=12.5,
                color=GREEN if better else AMBER, weight="bold")
        ax.set_title(title, loc="left", fontsize=16, weight="bold", pad=12)
        ax.set_ylabel(unit)
        ax.set_xticks(range(3), LABELS)
        ax.set_ylim(0, max(vals)*1.24)
        grid(ax)
    fig.supxlabel("Same 4.20-inch storm, identical conveyance assumptions", color=GRAY)
    save(fig, "scenario_comparison.png")


def plot_pipe_flows(data):
    sc = data["scenarios"]
    links = ("C1", "C2", "C3")
    fig, ax = plt.subplots(figsize=(12.5, 6.8), layout="constrained")
    width = 0.24
    for n, scenario in enumerate(ORDER):
        vals = [sc[scenario]["links"][link]["peak_flow_cfs"] for link in links]
        bars = ax.bar([i + (n - 1)*width for i in range(3)], vals, width=width,
                      color=COLORS[n], label=LABELS[n])
        for bar, v in zip(bars, vals):
            ax.annotate(f"{v:.2f}", (bar.get_x() + bar.get_width()/2, v),
                        xytext=(0, 7), textcoords="offset points",
                        ha="center", fontsize=11)
    baseline = sc["Baseline"]["links"]["C3"]["peak_flow_cfs"]
    green = sc["Green_All"]["links"]["C3"]["peak_flow_cfs"]
    ax.text(0.98, 0.9, f"C3 peak reduction: {(baseline-green)/baseline:.1%}",
            transform=ax.transAxes, ha="right", color=GREEN, weight="bold", fontsize=14)
    ax.set_title("Peak discharge through the pipe network", fontsize=21, weight="bold", pad=22)
    ax.set_ylabel("Maximum modeled flow (CFS)")
    ax.set_xticks(range(3), links)
    ax.set_ylim(0, 50)
    ax.legend(loc="upper left", frameon=False, ncol=3)
    grid(ax)
    ax.text(0.5, -0.16, "C3 time to peak: 2.00 h (baseline) → 3.50 h (all-six)",
            transform=ax.transAxes, ha="center", color=GRAY)
    save(fig, "pipe_peak_flows.png")


def read_rainfall():
    t, d = [], []
    for raw in RAINFALL.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        clock, depth = line.split()[:2]
        hours, mins = [int(v) for v in clock.split(":")]
        t.append(hours + mins/60)
        d.append(float(depth))
    if len(t) != 96 or abs(sum(d)-4.2) > 1e-4:
        raise ValueError("Rainfall input is expected to have 96 bins totaling 4.20 inches")
    return t, d


def plot_rain():
    t, d = read_rainfall()
    cumulative, total = [], 0.0
    for value in d:
        total += value
        cumulative.append(total)
    fig, ax = plt.subplots(figsize=(13.5, 5.8), layout="constrained")
    ax.bar(t, d, width=0.25, align="edge", color="#5c9bd6", edgecolor="white", lw=0.25)
    ax.set_xlim(0, 24)
    ax.set_ylim(0, max(d)*1.35)
    ax.set_xticks(range(0, 25, 3))
    ax.set_xlabel("Elapsed storm time (hours)")
    ax.set_ylabel("Rainfall volume (in / 15 minutes)")
    ax.set_title("4.20-inch, 24-hour design rainfall scenario", fontsize=21, weight="bold", pad=20)
    grid(ax)
    right = ax.twinx()
    right.step([0]+[x+0.25 for x in t], [0]+cumulative, where="post",
               color=GREEN, lw=2.7)
    right.set_ylim(0, 4.8)
    right.set_ylabel("Cumulative rainfall (in)")
    right.spines["top"].set_visible(False)
    ax.legend(handles=[
        plt.Rectangle((0, 0), 1, 1, color="#5c9bd6", label="15-minute increment"),
        Line2D([], [], color=GREEN, linewidth=2.7, label="Cumulative rainfall"),
    ], frameon=False, loc="center right")
    ax.text(0.015, 0.96,
            "NOAA Atlas 14 first-quartile, 50% temporal shape\n"
            "Interpolated from 30-minute cumulative fractions",
            transform=ax.transAxes, ha="left", va="top", color=NAVY, fontsize=12.5)
    save(fig, "design_rainfall.png")


def node(ax, x, y, width, height, text, face, edge, fontsize=14, ink=NAVY):
    patch = FancyBboxPatch((x,y), width,height, boxstyle="round,pad=0.13,rounding_size=0.19",
                           facecolor=face, edgecolor=edge, linewidth=1.9, zorder=3)
    ax.add_patch(patch)
    ax.text(x+width/2, y+height/2, text, ha="center", va="center",
            fontsize=fontsize, weight="bold", color=ink, zorder=4)


def arrow(ax, start, end, color, size=15, width=1.8):
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle="-|>", mutation_scale=size,
                                 linewidth=width, color=color, zorder=1))


def plot_network():
    fig, ax = plt.subplots(figsize=(17, 7.4))
    fig.subplots_adjust(left=0.03, right=0.97, top=0.87, bottom=0.12)
    fig.suptitle("Conceptual SWMM drainage network", fontsize=23, weight="bold", y=0.96)
    ax.set_xlim(0.1, 16.35)
    ax.set_ylim(0, 7.1)
    ax.axis("off")
    centers = (3.25, 7.75, 12.25, 15.6)
    y = 3.35
    diam = (3,4,5)
    lengths = (703,644,270)
    for i in range(3):
        arrow(ax, (centers[i]+0.65,y+0.46), (centers[i+1]-0.65,y+0.46),
              NAVY, 22, 2.7)
        ax.text((centers[i]+centers[i+1])/2, y+1.08,
                f"C{i+1}  |  Ø {diam[i]} ft  |  {lengths[i]} ft",
                ha="center", weight="bold", fontsize=12.5)
    areas = {"S1":8.956,"S2":14.879,"S3":19.773,
             "S4":12.639,"S5":11.76,"S6":14.6}
    for i in range(3):
        for top in (True,False):
            name=f"S{i+1 if top else i+4}"
            bx=(1.7,6.2,10.7)[i]
            by=5.72 if top else 0.75
            endpoint=(centers[i]-0.14, y+0.94 if top else y+0.06)
            origin=(bx+0.78, by if top else by+0.88)
            arrow(ax, origin, endpoint, TEAL, 14, 1.8)
            node(ax,bx,by,1.68,0.88,f"{name}\n{areas[name]:.2f} ac",
                 "#e6f5f2",TEAL,13)
    for i,label in enumerate(("J1","J2","J3")):
        node(ax,centers[i]-0.52,y+0.02,1.04,0.9,label,NAVY,NAVY,16,"white")
    node(ax,centers[3]-0.55,y+0.02,1.1,0.9,"O1","#fff2dc",AMBER,16)
    ax.text(centers[3],y-0.4,"FREE outfall",ha="center",color=AMBER,
            weight="bold",fontsize=12)
    ax.text(8.1,0.16,
            "Conceptual connectivity only  •  Not to scale  •  No verified pipe survey or river tailwater",
            ha="center",fontsize=12.5,color=GRAY)
    save(fig,"network_schematic.png")


def main():
    style()
    data=json.loads(METRICS.read_text(encoding="utf-8"))
    plot_scenarios(data)
    plot_pipe_flows(data)
    plot_rain()
    plot_network()


if __name__ == "__main__":
    main()
