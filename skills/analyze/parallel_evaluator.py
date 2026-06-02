"""Parallel processing safety evaluator for PDF operations."""

import psutil


def evaluate_parallel_safety() -> dict:
    """Evaluate whether the system can safely run PDF processing in parallel.

    Returns:
        dict with keys:
          - can_parallel: bool
          - reason: str
          - recommendations: list[str]
          - cpu_count: int
          - memory_gb: float
    """
    cpu_count = psutil.cpu_count(logical=True) or 1
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)

    recommendations = []
    can_parallel = True
    reasons = []

    # MinerU is strictly serial per docs
    reasons.append("MinerU currently supports only serial execution")
    can_parallel = False

    # CPU check
    if cpu_count < 4:
        recommendations.append(f"CPU cores ({cpu_count}) is low; parallel may not help")
    else:
        recommendations.append(f"CPU cores ({cpu_count}) sufficient for parallel tasks")

    # Memory check
    if memory_gb < 8:
        recommendations.append(f"Memory ({memory_gb:.1f}GB) is low; parallel may cause OOM")
    else:
        recommendations.append(f"Memory ({memory_gb:.1f}GB) is adequate")

    reason = ". ".join(reasons) if reasons else "System can support parallel processing"

    return {
        "can_parallel": can_parallel,
        "reason": reason,
        "recommendations": recommendations,
        "cpu_count": cpu_count,
        "memory_gb": round(memory_gb, 2),
    }
