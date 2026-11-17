import ctypes
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import numpy as np

from .parser import FlowshopInstance

AVAILABLE_ALGORITHMS = ["tabu_original", "tabu_optimized", "tabu_neh"]


@dataclass
class SolveResult:
    instance_name: str
    algo: str
    tenure_requested: int
    tenure_effective: int
    max_iterations: int
    initial_makespan: int
    best_makespan: int
    elapsed_sec: float
    best_schedule: np.ndarray  # Shape: (num_jobs,), dtype=int32
    history: np.ndarray        # Shape: (max_iterations + 1,), dtype=int32

    @property
    def improvement_pct(self) -> float:
        if self.initial_makespan <= 0:
            return 0.0
        return ((self.initial_makespan - self.best_makespan) / self.initial_makespan) * 100.0


def _locate_shared_lib() -> Path:
    if sys.platform.startswith("win"):
        lib_name = "libflowshop.dll"
    elif sys.platform == "darwin":
        lib_name = "libflowshop.dylib"
    else:
        lib_name = "libflowshop.so"

    cwd_candidate = Path.cwd() / "build" / "lib" / lib_name
    if cwd_candidate.exists():
        return cwd_candidate

    repo_root = Path(__file__).resolve().parents[3]
    repo_candidate = repo_root / "build" / "lib" / lib_name
    if repo_candidate.exists():
        return repo_candidate

    raise FileNotFoundError(
        f"C++ shared library '{lib_name}' not found. Run 'make' in the project root first."
    )


def _load_lib() -> ctypes.CDLL:
    lib_path = _locate_shared_lib()
    if sys.platform.startswith("win"):
        os.add_dll_directory(str(lib_path.parent))
        lib = ctypes.CDLL(str(lib_path), winmode=0)
    else:
        lib = ctypes.CDLL(str(lib_path))

    lib.solve_pfsp.argtypes = [
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int,
        np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags="C_CONTIGUOUS"),
        ctypes.c_int,
        ctypes.c_int,
        np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags="C_CONTIGUOUS"),
        np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags="C_CONTIGUOUS"),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.solve_pfsp.restype = ctypes.c_int
    return lib


_LIB: ctypes.CDLL | None = None


def run_solver(
    instance: FlowshopInstance,
    algo: str = "tabu_original",
    max_iterations: int = 300,
    tabu_tenure: int = 0,
) -> SolveResult:
    global _LIB
    if _LIB is None:
        _LIB = _load_lib()

    algo_clean = algo.strip().lower()
    if algo_clean not in AVAILABLE_ALGORITHMS:
        raise ValueError(
            f"Unknown algorithm '{algo}'. Available: {AVAILABLE_ALGORITHMS}"
        )

    flat_matrix = np.ascontiguousarray(instance.proc_times.ravel(), dtype=np.int32)
    out_schedule = np.zeros(instance.num_jobs, dtype=np.int32)
    out_history = np.zeros(max_iterations + 1, dtype=np.int32)
    elapsed_c = ctypes.c_double(0.0)

    best_ms = _LIB.solve_pfsp(
        algo_clean.encode("utf-8"),
        instance.num_jobs,
        instance.num_machines,
        flat_matrix,
        max_iterations,
        tabu_tenure,
        out_schedule,
        out_history,
        ctypes.byref(elapsed_c),
    )

    if best_ms < 0:
        raise RuntimeError(f"C++ solver failed for algorithm '{algo_clean}'.")

    effective_tenure = (
        tabu_tenure if tabu_tenure > 0 else max(5, (instance.num_jobs * 10) // 11)
    )

    return SolveResult(
        instance_name=instance.name,
        algo=algo_clean,
        tenure_requested=tabu_tenure,
        tenure_effective=effective_tenure,
        max_iterations=max_iterations,
        initial_makespan=int(out_history[0]),
        best_makespan=int(best_ms),
        elapsed_sec=float(elapsed_c.value),
        best_schedule=out_schedule,
        history=out_history,
    )
