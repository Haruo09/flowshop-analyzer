from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from ._ffi import SolveResult
from .parser import FlowshopInstance


def plot_convergence(
    instance: FlowshopInstance,
    results: list[SolveResult],
    output_path: str | Path,
) -> Path:
    """Plots single or multi-curve convergence (Best Makespan vs. Iteration)."""
    if not results:
        raise ValueError("At least one SolveResult is required for plotting.")

    fig, ax = plt.subplots(figsize=(11, 6))
    colors = plt.cm.tab10.colors  # type: ignore[attr-defined]
    linestyles = ["-", "--", "-.", ":"]

    overall_best = min(r.best_makespan for r in results)

    for idx, res in enumerate(results):
        iterations = np.arange(len(res.history))
        tenure_tag = (
            f"auto={res.tenure_effective}"
            if res.tenure_requested <= 0
            else str(res.tenure_effective)
        )
        label = (
            f"{res.algo} (tenure={tenure_tag}) | "
            f"Best: {res.best_makespan} (-{res.improvement_pct:.1f}%, {res.elapsed_sec:.3f}s)"
        )
        ax.step(
            iterations,
            res.history,
            where="post",
            color=colors[idx % len(colors)],
            linestyle=linestyles[idx % len(linestyles)],
            linewidth=2.2,
            label=label,
        )

    ax.axhline(
        overall_best,
        color="crimson",
        linestyle=":",
        linewidth=1.4,
        label=f"Overall Best Makespan ($C_{{max}}$ = {overall_best})",
    )

    ax.set_title(
        f"Tabu Search Convergence — {instance.name} "
        f"({instance.num_jobs} Jobs × {instance.num_machines} Machines)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Best Makespan ($C_{max}$)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(loc="upper right", frameon=True, fontsize=9.5)

    plt.tight_layout()
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file


def plot_gantt(
    instance: FlowshopInstance,
    result: SolveResult,
    output_path: str | Path,
) -> Path:
    """Renders a Machine-by-Machine Schedule Gantt Chart for a solved permutation."""
    n = instance.num_jobs
    m = instance.num_machines
    schedule = result.best_schedule
    proc = instance.proc_times

    start_times = np.zeros((n, m), dtype=np.int32)
    end_times = np.zeros((n, m), dtype=np.int32)

    for seq_idx, job_id in enumerate(schedule):
        for mach in range(m):
            prev_job_end = end_times[seq_idx - 1, mach] if seq_idx > 0 else 0
            prev_mach_end = end_times[seq_idx, mach - 1] if mach > 0 else 0
            start = max(prev_job_end, prev_mach_end)
            duration = proc[job_id, mach]
            start_times[seq_idx, mach] = start
            end_times[seq_idx, mach] = start + duration

    fig_height = max(4.5, 0.55 * m + 1.8)
    fig, ax = plt.subplots(figsize=(13, fig_height))
    cmap = plt.get_cmap("tab20" if n <= 20 else "hsv")

    for seq_idx, job_id in enumerate(schedule):
        color = cmap(job_id % 20 if n <= 20 else job_id / max(1, n))
        for mach in range(m):
            start = start_times[seq_idx, mach]
            dur = proc[job_id, mach]
            ax.barh(
                y=mach,
                width=dur,
                left=start,
                height=0.62,
                color=color,
                edgecolor="black",
                linewidth=0.7,
                alpha=0.9,
            )
            if n <= 25 and dur > 0:
                ax.text(
                    start + dur / 2.0,
                    mach,
                    f"J{job_id}",
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=8,
                    fontweight="bold",
                )

    ax.axvline(
        result.best_makespan,
        color="crimson",
        linestyle="--",
        linewidth=1.8,
        label=f"Makespan ($C_{{max}}$) = {result.best_makespan}",
    )

    ax.set_yticks(range(m))
    ax.set_yticklabels([f"Machine {i}" for i in range(m)])
    ax.invert_yaxis()
    ax.set_xlabel("Time Units", fontsize=11)
    ax.set_title(
        f"Flowshop Schedule Gantt Chart — {instance.name} "
        f"[{result.algo}, tenure={result.tenure_effective}, $C_{{max}}$={result.best_makespan}]",
        fontsize=12.5,
        fontweight="bold",
        pad=12,
    )
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right", frameon=True)

    plt.tight_layout()
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file
