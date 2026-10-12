"""Evaluation Service: loads the supported model, prepares input, runs prediction."""

from app.evaluation.runner import run_evaluation

__all__ = ["run_evaluation"]
