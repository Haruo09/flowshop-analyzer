from dataclasses import dataclass
from pathlib import Path
import numpy as np


@dataclass(frozen=True)
class FlowshopInstance:
    name: str
    description: str
    num_jobs: int
    num_machines: int
    proc_times: np.ndarray  # Shape: (num_jobs, num_machines), dtype=int32


def load_instances(file_path: str | Path) -> list[FlowshopInstance]:
    """Parses OR-Library Flowshop instances from a text dataset."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path.resolve()}")

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    instances: list[FlowshopInstance] = []
    idx = 0
    total_lines = len(lines)

    while idx < total_lines:
        clean = lines[idx].strip()
        if clean.startswith("instance "):
            name = clean[len("instance ") :].strip()
            idx += 1

            description = ""
            while idx < total_lines:
                desc_line = lines[idx].strip()
                idx += 1
                if desc_line and "+++" not in desc_line:
                    description = desc_line
                    break

            while idx < total_lines and not lines[idx].strip():
                idx += 1
            dims = lines[idx].strip().split()
            num_jobs, num_machines = int(dims[0]), int(dims[1])
            idx += 1

            expected_tokens = 2 * num_jobs * num_machines
            tokens: list[int] = []
            while idx < total_lines and len(tokens) < expected_tokens:
                row_str = lines[idx].strip()
                idx += 1
                if not row_str or "+++" in row_str:
                    continue
                tokens.extend(int(tok) for tok in row_str.split())

            if len(tokens) < expected_tokens:
                raise ValueError(
                    f"Malformed instance '{name}': expected {expected_tokens} values, got {len(tokens)}."
                )

            proc_times = np.zeros((num_jobs, num_machines), dtype=np.int32)
            cursor = 0
            for j in range(num_jobs):
                for _ in range(num_machines):
                    machine_id = tokens[cursor]
                    duration = tokens[cursor + 1]
                    proc_times[j, machine_id] = duration
                    cursor += 2

            instances.append(
                FlowshopInstance(
                    name=name,
                    description=description,
                    num_jobs=num_jobs,
                    num_machines=num_machines,
                    proc_times=proc_times,
                )
            )
        else:
            idx += 1

    return instances


def get_instance(file_path: str | Path, instance_name: str) -> FlowshopInstance:
    """Finds an instance by name (case-insensitive)."""
    target = instance_name.strip().lower()
    instances = load_instances(file_path)
    for inst in instances:
        if inst.name.lower() == target:
            return inst

    available = ", ".join(inst.name for inst in instances)
    raise KeyError(
        f"Instance '{instance_name}' not found. Available instances: {available}"
    )
