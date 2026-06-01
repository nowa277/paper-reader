"""Tests for parallel evaluator."""

import psutil
from unittest.mock import patch, MagicMock
from skills.analyze.parallel_evaluator import evaluate_parallel_safety


class TestEvaluateParallelSafety:
    """Tests for evaluate_parallel_safety()."""

    def test_returns_dict_with_keys(self):
        """Result contains all required keys."""
        result = evaluate_parallel_safety()
        assert "can_parallel" in result
        assert "reason" in result
        assert "recommendations" in result
        assert "cpu_count" in result
        assert "memory_gb" in result

    def test_cpu_count_is_int(self):
        """cpu_count is an integer."""
        result = evaluate_parallel_safety()
        assert isinstance(result["cpu_count"], int)

    def test_memory_gb_is_float(self):
        """memory_gb is a float."""
        result = evaluate_parallel_safety()
        assert isinstance(result["memory_gb"], float)

    def test_recommendations_is_list(self):
        """recommendations is a list."""
        result = evaluate_parallel_safety()
        assert isinstance(result["recommendations"], list)
