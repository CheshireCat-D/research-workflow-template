#!/usr/bin/env python3
"""Render an explicitly synthetic publication-figure example with Matplotlib.

Optional demonstration only: no downloads, analysis claims or real-paper data.
Requires an already available Matplotlib; the workflow itself stays stdlib-only.
"""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="A new directory whose parent already exists")
    args = parser.parse_args()
    output = args.output_dir
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        parser.error("Choose a new output directory with an existing parent")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        parser.error("This optional example needs Matplotlib in the selected Python; no package was installed")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.labelsize": 8, "axes.titlesize": 9,
                         "svg.fonttype": "none", "pdf.fonttype": 42})
    x = [0, 1, 2, 3, 4]
    y = [1.00, 0.77, 0.57, 0.43, 0.31]
    extent = [0.05, 0.06, 0.05, 0.04, 0.04]
    fig, axes = plt.subplots(1, 2, figsize=(180 / 25.4, 72 / 25.4),
                             layout="constrained")
    axes[0].errorbar(x, y, yerr=extent, marker="o", markersize=4,
                     color="#2166ac", linewidth=1.2, capsize=3)
    axes[0].set(xlabel="Step (arbitrary unit)", ylabel="Response (arbitrary unit)",
                title="a  Synthetic response", ylim=(0, 1.15))
    axes[1].plot(x, extent, "s-", color="#b2182b", linewidth=1.2, markersize=4)
    axes[1].set(xlabel="Step (arbitrary unit)", ylabel="Illustrative extent (arbitrary unit)",
                title="b  Specified extents", ylim=(0, 0.085))
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(direction="out", length=3, width=0.7)
    output.mkdir()
    try:
        for suffix in ("svg", "pdf", "png"):
            fig.savefig(output / ("synthetic-figure." + suffix), dpi=300)
        (output / "source-data.csv").write_text("step,response,illustrative_extent\n" +
            "".join(f"{a},{b:.2f},{c:.2f}\n" for a,b,c in zip(x,y,extent)))
        (output / "README.txt").write_text(
            "Synthetic demonstration only. Extents are specified illustrative values, "
            "not SD, SE, confidence intervals or observed uncertainty. No study or significance test was performed.\n")
    except BaseException:
        shutil.rmtree(output)
        raise
    finally:
        plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
