import csv
from pathlib import Path
import numpy as np
import pytest
from typer.testing import CliRunner

from flowshop_analyzer.cli import app
from flowshop_analyzer.parser import FlowshopInstance, get_instance, load_instances
from flowshop_analyzer._ffi import AVAILABLE_ALGORITHMS, run_solver


def test_or_library_parsing():
    """1) Verify parsing of all 31 OR-Library benchmark instances."""
    dataset_path = Path("instancias.txt")
    assert dataset_path.exists(), "instancias.txt dataset file not found."

    instances = load_instances(dataset_path)
    assert len(instances) == 31, f"Expected 31 instances, found {len(instances)}"

    for inst in instances:
        assert inst.num_jobs > 0
        assert inst.num_machines > 0
        assert inst.proc_times.shape == (inst.num_jobs, inst.num_machines)
        assert np.all(inst.proc_times >= 0)

    # Check known instance dimensions
    car1 = get_instance(dataset_path, "car1")
    assert car1.num_jobs == 11
    assert car1.num_machines == 5

    car8 = get_instance(dataset_path, "car8")
    assert car8.num_jobs == 8
    assert car8.num_machines == 8

    hel1 = get_instance(dataset_path, "hel1")
    assert hel1.num_jobs == 100
    assert hel1.num_machines == 10

    hel2 = get_instance(dataset_path, "hel2")
    assert hel2.num_jobs == 20
    assert hel2.num_machines == 10

    reC01 = get_instance(dataset_path, "reC01")
    assert reC01.num_jobs == 20
    assert reC01.num_machines == 5

    reC41 = get_instance(dataset_path, "reC41")
    assert reC41.num_jobs == 75
    assert reC41.num_machines == 20

    with pytest.raises(KeyError):
        get_instance(dataset_path, "nonexistent_instance")


def test_exact_makespan_handcrafted_3x3():
    """2) Verify exact makespan calculation on a hand-computed 3x3 instance."""
    # Hand-computed instance with known flowshop makespan values:
    # Job 0: [3, 2, 2]
    # Job 1: [2, 1, 4]
    # Job 2: [4, 3, 1]
    #
    # Sequence [0, 1, 2] completion times:
    # J0: M0=3,  M1=5,  M2=7
    # J1: M0=5,  M1=6,  M2=11
    # J2: M0=9,  M1=12, M2=13 -> Makespan = 13
    #
    # Across all 6 permutations, min makespan is 13 (at [0, 1, 2] and [1, 2, 0]).
    proc_times = np.array(
        [
            [3, 2, 2],
            [2, 1, 4],
            [4, 3, 1],
        ],
        dtype=np.int32,
    )
    inst = FlowshopInstance(
        name="handcrafted_3x3",
        num_jobs=3,
        num_machines=3,
        proc_times=proc_times,
        description="Handcrafted 3x3 test instance",
    )

    # tabu_original starts at [0, 1, 2] -> initial makespan must be exactly 13
    res_orig = run_solver(inst, algo="tabu_original", max_iterations=5, tabu_tenure=0)
    assert res_orig.initial_makespan == 13
    assert res_orig.best_makespan == 13

    # tabu_optimized starts at [0, 1, 2] -> initial makespan must be exactly 13
    res_opt = run_solver(inst, algo="tabu_optimized", max_iterations=5, tabu_tenure=0)
    assert res_opt.initial_makespan == 13
    assert res_opt.best_makespan == 13

    # tabu_neh constructs initial sequence with NEH:
    # Total times: J2=8, J0=7, J1=7 -> NEH yields [1, 2, 0] with makespan 13
    res_neh = run_solver(inst, algo="tabu_neh", max_iterations=5, tabu_tenure=0)
    assert res_neh.initial_makespan == 13
    assert res_neh.best_makespan == 13


def test_output_schedule_validity():
    """3) Verify that every result is a valid permutation of 0..N-1."""
    dataset_path = Path("instancias.txt")
    test_instances = ["car1", "car7", "hel2", "reC01"]

    for algo in AVAILABLE_ALGORITHMS:
        for name in test_instances:
            inst = get_instance(dataset_path, name)
            res = run_solver(inst, algo=algo, max_iterations=20, tabu_tenure=0)

            schedule = res.best_schedule
            assert len(schedule) == inst.num_jobs
            assert sorted(schedule.tolist()) == list(range(inst.num_jobs))
            assert len(set(schedule.tolist())) == inst.num_jobs


def test_deterministic_parity_original_vs_optimized():
    """4) Verify tabu_original and tabu_optimized have identical makespan and history."""
    dataset_path = Path("instancias.txt")
    test_instances = ["car1", "car2", "car5", "car7", "hel2", "reC01", "reC07"]

    for name in test_instances:
        inst = get_instance(dataset_path, name)
        res_orig = run_solver(inst, algo="tabu_original", max_iterations=30, tabu_tenure=0)
        res_opt = run_solver(inst, algo="tabu_optimized", max_iterations=30, tabu_tenure=0)

        assert res_orig.initial_makespan == res_opt.initial_makespan
        assert res_orig.best_makespan == res_opt.best_makespan
        assert np.array_equal(res_orig.best_schedule, res_opt.best_schedule)
        assert np.array_equal(res_orig.history, res_opt.history)


def test_cli_csv_export_generation(tmp_path: Path):
    """5) Verify CLI CSV export generation in single and multi-algorithm modes."""
    runner = CliRunner()

    # Single-algorithm mode
    single_csv = tmp_path / "single_benchmark.csv"
    res_single = runner.invoke(
        app,
        [
            "benchmark",
            "--file",
            "instancias.txt",
            "-a",
            "tabu_original",
            "-i",
            "5",
            "--csv",
            str(single_csv),
        ],
    )
    assert res_single.exit_code == 0
    assert single_csv.exists()

    with open(single_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 31
        expected_cols = {
            "instance",
            "jobs",
            "machines",
            "initial_makespan",
            "best_makespan",
            "improvement_pct",
            "runtime_sec",
            "tabu_original_runtime_sec",
            "speedup",
        }
        assert expected_cols.issubset(rows[0].keys())
        assert rows[0]["instance"] == "car1"
        assert int(rows[0]["jobs"]) == 11
        assert int(rows[0]["machines"]) == 5

    # Multi-algorithm mode
    multi_csv = tmp_path / "multi_benchmark.csv"
    res_multi = runner.invoke(
        app,
        [
            "benchmark",
            "--file",
            "instancias.txt",
            "-a",
            "tabu_original",
            "-a",
            "tabu_optimized",
            "-a",
            "tabu_neh",
            "-i",
            "5",
            "--csv",
            str(multi_csv),
        ],
    )
    assert res_multi.exit_code == 0
    assert multi_csv.exists()

    with open(multi_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 31
        expected_cols = {
            "instance",
            "jobs",
            "machines",
            "initial_makespan",
            "best_makespan",
            "improvement_pct",
            "tabu_original_runtime_sec",
            "tabu_optimized_runtime_sec",
            "tabu_neh_runtime_sec",
            "speedup",
        }
        assert expected_cols.issubset(rows[0].keys())
