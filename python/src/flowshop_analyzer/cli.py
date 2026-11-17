import csv as csv_module
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ._ffi import AVAILABLE_ALGORITHMS, SolveResult, run_solver
from .parser import get_instance, load_instances
from .plotting import plot_convergence, plot_gantt

app = typer.Typer(
    name="flowshop-analyzer",
    help="CLI tool to solve, benchmark, and visualize PFSP heuristics.",
    add_completion=False,
)
console = Console()


@app.command("list-instances")
def list_instances(
    file: Path = typer.Option(
        Path("instancias.txt"), "--file", "-f", help="Path to OR-Library dataset file."
    ),
) -> None:
    """List all benchmark instances available in the dataset file."""
    instances = load_instances(file)
    table = Table(title=f"Available PFSP Instances ({len(instances)} total)")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Instance", style="cyan bold")
    table.add_column("Jobs (N)", style="magenta", justify="right")
    table.add_column("Machines (M)", style="green", justify="right")
    table.add_column("Description", style="white")

    for idx, inst in enumerate(instances, start=1):
        table.add_row(
            str(idx),
            inst.name,
            str(inst.num_jobs),
            str(inst.num_machines),
            inst.description,
        )

    console.print(table)


@app.command("solve")
def solve(
    instance_name: str = typer.Argument(
        ..., help="Instance name (e.g., car1, hel2, reC01)."
    ),
    file: Path = typer.Option(
        Path("instancias.txt"), "--file", "-f", help="Path to dataset file."
    ),
    algos: list[str] = typer.Option(
        ["tabu_original"],
        "--algo",
        "-a",
        help=f"Algorithm(s) to run (repeatable). Choices: {', '.join(AVAILABLE_ALGORITHMS)}",
    ),
    tenures: list[int] = typer.Option(
        [0],
        "--tenure",
        "-t",
        help="Tabu tenure(s) to test (repeatable; 0 = auto max(5, N*10//11)).",
    ),
    iterations: int = typer.Option(
        300, "--iterations", "-i", min=1, help="Maximum Tabu Search iterations."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Path to save convergence plot (.png)."
    ),
    gantt: Optional[Path] = typer.Option(
        None, "--gantt", "-g", help="Path to save Gantt chart for the best schedule (.png)."
    ),
) -> None:
    """Solve a single PFSP instance across one or more (algorithm, tenure) configurations."""
    try:
        instance = get_instance(file, instance_name)
    except (FileNotFoundError, KeyError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print(
        Panel.fit(
            f"[bold green]Flowshop Analyzer[/bold green] — Instance [yellow]{instance.name}[/yellow] "
            f"({instance.description})\n"
            f"Dimensions: [cyan]{instance.num_jobs} jobs × {instance.num_machines} machines[/cyan] | "
            f"Max Iterations: {iterations}",
            border_style="blue",
        )
    )

    results: list[SolveResult] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        for algo in algos:
            for tenure in tenures:
                task_id = progress.add_task(
                    description=f"Running {algo} (tenure={tenure or 'auto'})...",
                    total=None,
                )
                try:
                    res = run_solver(
                        instance,
                        algo=algo,
                        max_iterations=iterations,
                        tabu_tenure=tenure,
                    )
                except ValueError as exc:
                    console.print(f"[bold red]Error:[/bold red] {exc}")
                    raise typer.Exit(code=1)
                results.append(res)
                progress.remove_task(task_id)

    table = Table(title=f"Optimization Results: {instance.name}")
    table.add_column("Algorithm", style="cyan")
    table.add_column("Tenure", style="magenta", justify="right")
    table.add_column("Initial C_max", style="white", justify="right")
    table.add_column("Best C_max", style="bold green", justify="right")
    table.add_column("Improvement", style="yellow", justify="right")
    table.add_column("Runtime (s)", style="blue", justify="right")

    for r in results:
        tenure_disp = (
            f"auto ({r.tenure_effective})"
            if r.tenure_requested <= 0
            else str(r.tenure_effective)
        )
        table.add_row(
            r.algo,
            tenure_disp,
            str(r.initial_makespan),
            str(r.best_makespan),
            f"-{r.improvement_pct:.2f}%",
            f"{r.elapsed_sec:.4f}",
        )

    console.print(table)

    best_run = min(results, key=lambda r: r.best_makespan)
    seq_str = ", ".join(str(j) for j in best_run.best_schedule.tolist())
    console.print(
        f"[bold]Best Schedule[/bold] ({best_run.algo}, tenure={best_run.tenure_effective}, "
        f"C_max={best_run.best_makespan}): [{seq_str}]"
    )

    if output:
        saved_conv = plot_convergence(instance, results, output)
        console.print(f"[bold green]Convergence plot saved to:[/bold green] {saved_conv}")

    if gantt:
        saved_gantt = plot_gantt(instance, best_run, gantt)
        console.print(f"[bold green]Gantt chart saved to:[/bold green] {saved_gantt}")


@app.command("benchmark")
def benchmark(
    file: Path = typer.Option(
        Path("instancias.txt"), "--file", "-f", help="Path to dataset file."
    ),
    algos: list[str] = typer.Option(
        ["tabu_original"],
        "--algo",
        "-a",
        help=f"Algorithm(s) to benchmark (repeatable). Choices: {', '.join(AVAILABLE_ALGORITHMS)}",
    ),
    tenure: int = typer.Option(
        0, "--tenure", "-t", help="Tabu tenure (0 = auto)."
    ),
    iterations: int = typer.Option(
        300, "--iterations", "-i", min=1, help="Maximum iterations per instance."
    ),
    csv: Optional[Path] = typer.Option(
        None, "--csv", "-c", help="Path to save benchmark metrics (.csv)."
    ),
) -> None:
    """Benchmark one or compare multiple algorithms across all instances in the dataset."""
    instances = load_instances(file)
    tenure_label = "auto" if tenure <= 0 else str(tenure)

    if len(algos) == 1:
        algo = algos[0]
        table = Table(
            title=f"Full Dataset Benchmark ({algo}, iterations={iterations}, tenure={tenure_label})"
        )
        table.add_column("Instance", style="cyan bold")
        table.add_column("N × M", style="magenta", justify="center")
        table.add_column("Initial C_max", justify="right")
        table.add_column("Best C_max", style="bold green", justify="right")
        table.add_column("Improvement", style="yellow", justify="right")
        table.add_column("Runtime (s)", style="blue", justify="right")

        total_time = 0.0
        csv_rows: list[dict] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Benchmarking instances...", total=len(instances))
            for inst in instances:
                res = run_solver(inst, algo=algo, max_iterations=iterations, tabu_tenure=tenure)
                total_time += res.elapsed_sec
                table.add_row(
                    inst.name,
                    f"{inst.num_jobs}×{inst.num_machines}",
                    str(res.initial_makespan),
                    str(res.best_makespan),
                    f"-{res.improvement_pct:.2f}%",
                    f"{res.elapsed_sec:.4f}",
                )
                if csv:
                    csv_rows.append(
                        {
                            "instance": inst.name,
                            "jobs": inst.num_jobs,
                            "machines": inst.num_machines,
                            "initial_makespan": res.initial_makespan,
                            "best_makespan": res.best_makespan,
                            "improvement_pct": f"{res.improvement_pct:.2f}",
                            "runtime_sec": f"{res.elapsed_sec:.4f}",
                            f"{algo}_runtime_sec": f"{res.elapsed_sec:.4f}",
                            "speedup": "1.00",
                        }
                    )
                progress.advance(task)

        console.print(table)
        console.print(f"[bold]Total C++ Solver Time ({algo}):[/bold] {total_time:.4f}s")

        if csv:
            csv.parent.mkdir(parents=True, exist_ok=True)
            fieldnames = [
                "instance",
                "jobs",
                "machines",
                "initial_makespan",
                "best_makespan",
                "improvement_pct",
                "runtime_sec",
                f"{algo}_runtime_sec",
                "speedup",
            ]
            with open(csv, mode="w", newline="", encoding="utf-8") as f:
                writer = csv_module.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            console.print(f"[bold green]Benchmark results saved to CSV:[/bold green] {csv}")
        return

    # Multi-algorithm head-to-head comparison mode
    table = Table(
        title=f"Algorithm Runtime & Quality Comparison (iterations={iterations}, tenure={tenure_label})"
    )
    table.add_column("Instance", style="cyan bold")
    table.add_column("N × M", style="magenta", justify="center")
    table.add_column("Best C_max", style="bold green", justify="right")
    for a in algos:
        table.add_column(f"{a} (s)", style="blue", justify="right")
    table.add_column(f"Speedup (vs {algos[0]})", style="yellow bold", justify="right")

    totals = {a: 0.0 for a in algos}
    csv_rows = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(
            f"Comparing {', '.join(algos)} across {len(instances)} instances...",
            total=len(instances),
        )
        for inst in instances:
            run_map: dict[str, SolveResult] = {}
            for a in algos:
                res = run_solver(inst, algo=a, max_iterations=iterations, tabu_tenure=tenure)
                run_map[a] = res
                totals[a] += res.elapsed_sec

            best_ms = min(r.best_makespan for r in run_map.values())
            base_time = run_map[algos[0]].elapsed_sec
            best_other_time = min(run_map[a].elapsed_sec for a in algos[1:])
            speedup = (base_time / best_other_time) if best_other_time > 0 else 0.0

            row = [
                inst.name,
                f"{inst.num_jobs}×{inst.num_machines}",
                str(best_ms),
                *[f"{run_map[a].elapsed_sec:.4f}" for a in algos],
                f"{speedup:.2f}x",
            ]
            table.add_row(*row)

            if csv:
                base_res = run_map[algos[0]]
                init_ms = base_res.initial_makespan
                imp_pct = (
                    ((init_ms - best_ms) / init_ms) * 100.0 if init_ms > 0 else 0.0
                )
                row_dict = {
                    "instance": inst.name,
                    "jobs": inst.num_jobs,
                    "machines": inst.num_machines,
                    "initial_makespan": init_ms,
                    "best_makespan": best_ms,
                    "improvement_pct": f"{imp_pct:.2f}",
                }
                for a in algos:
                    row_dict[f"{a}_runtime_sec"] = f"{run_map[a].elapsed_sec:.4f}"
                row_dict["speedup"] = f"{speedup:.2f}"
                csv_rows.append(row_dict)

            progress.advance(task)

    console.print(table)
    summary_parts = [f"{a}: [bold]{totals[a]:.4f}s[/bold]" for a in algos]
    overall_speedup = (
        totals[algos[0]] / min(totals[a] for a in algos[1:])
        if len(algos) > 1
        else 1.0
    )
    console.print(
        f"[bold]Total Dataset Runtime:[/bold] {' | '.join(summary_parts)} "
        f"([yellow]{overall_speedup:.2f}x overall speedup[/yellow])"
    )

    if csv:
        csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "instance",
            "jobs",
            "machines",
            "initial_makespan",
            "best_makespan",
            "improvement_pct",
            *[f"{a}_runtime_sec" for a in algos],
            "speedup",
        ]
        with open(csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv_module.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        console.print(f"[bold green]Benchmark results saved to CSV:[/bold green] {csv}")



if __name__ == "__main__":
    app()
