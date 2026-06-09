"""Token estimator for triggering subagent parallel patterns.

Based on spec §15.1 Token-aware trigger rules:
- < 50K tokens: single LLM
- 50K-200K: Map-Reduce (3-5 subagents)
- 200K-500K: Map-Reduce or Hierarchical
- > 500K: MUST Hierarchical

Reference:
- skills/analyze/verification/token_estimator.py
"""

import tiktoken
from enum import Enum
from typing import Optional


class TriggerMode(Enum):
    """Parallel execution mode based on token count."""
    SINGLE = "single"              # < 50K tokens
    MAP_REDUCE = "map_reduce"       # 50K-200K tokens
    MAP_REDUCE_OR_HIERARCHICAL = "map_reduce_or_hierarchical"  # 200K-500K
    HIERARCHICAL = "hierarchical"   # > 500K tokens


# Token thresholds from spec §15.1
TOKEN_THRESHOLD_SINGLE = 50_000
TOKEN_THRESHOLD_MAP_REDUCE = 200_000
TOKEN_THRESHOLD_HIERARCHICAL = 500_000


class TokenEstimator:
    """Estimate token count for triggering subagent parallel patterns."""

    def __init__(self, model: str = "cl100k_base"):
        """Initialize with tiktoken model.

        Args:
            model: tiktoken encoding model. Default: cl100k_base (GPT-4)
        """
        self._encoder: Optional[tiktoken.Encoding] = None
        self._model = model

    def _get_encoder(self) -> tiktoken.Encoding:
        """Lazy-load tiktoken encoder."""
        if self._encoder is None:
            self._encoder = tiktoken.get_encoding(self._model)
        return self._encoder

    def estimate(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Input text to estimate tokens for.

        Returns:
            Estimated token count.
        """
        encoder = self._get_encoder()
        return len(encoder.encode(text))

    def estimate_file(self, file_path: str) -> int:
        """Estimate token count for a file.

        Args:
            file_path: Path to text/markdown file.

        Returns:
            Estimated token count.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self.estimate(text)

    def get_trigger_mode(self, token_count: int) -> TriggerMode:
        """Determine trigger mode based on token count.

        Args:
            token_count: Estimated token count.

        Returns:
            TriggerMode enum value.
        """
        if token_count < TOKEN_THRESHOLD_SINGLE:
            return TriggerMode.SINGLE
        elif token_count < TOKEN_THRESHOLD_MAP_REDUCE:
            return TriggerMode.MAP_REDUCE
        elif token_count < TOKEN_THRESHOLD_HIERARCHICAL:
            return TriggerMode.MAP_REDUCE_OR_HIERARCHICAL
        else:
            return TriggerMode.HIERARCHICAL

    def get_chunk_count(self, token_count: int, chunk_size: int = 100_000) -> int:
        """Calculate number of chunks for given token count.

        Args:
            token_count: Total token count.
            chunk_size: Target tokens per chunk. Default: 100K.

        Returns:
            Number of chunks needed.
        """
        if token_count <= chunk_size:
            return 1
        return (token_count + chunk_size - 1) // chunk_size


def quick_estimate(text: str) -> int:
    """Quick token estimation using word count approximation.

    This is faster than tiktoken for rough estimates.
    Rule of thumb: 1 token ≈ 0.75 words for English.

    Args:
        text: Input text.

    Returns:
        Rough token estimate (may underestimate for non-English).
    """
    words = len(text.split())
    return int(words * 1.33)  # Conservative estimate


def should_split_subagent(token_count: int) -> bool:
    """Determine if subagent splitting is needed.

    Args:
        token_count: Estimated token count.

    Returns:
        True if task should be split across subagents.
    """
    return token_count >= TOKEN_THRESHOLD_MAP_REDUCE


# Module-level default estimator
_default_estimator: Optional[TokenEstimator] = None


def get_default_estimator() -> TokenEstimator:
    """Get or create default token estimator."""
    global _default_estimator
    if _default_estimator is None:
        _default_estimator = TokenEstimator()
    return _default_estimator


def estimate_and_decide(text: str) -> tuple[int, TriggerMode, int]:
    """One-shot estimate tokens, decide mode, calculate chunks.

    Args:
        text: Input text to analyze.

    Returns:
        Tuple of (token_count, trigger_mode, chunk_count).
    """
    estimator = get_default_estimator()
    tokens = estimator.estimate(text)
    mode = estimator.get_trigger_mode(tokens)
    chunks = estimator.get_chunk_count(tokens)
    return tokens, mode, chunks