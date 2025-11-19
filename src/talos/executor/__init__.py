"""Executor module for Talos.

This module provides functionality to simulate the executor/Talos loop,
applying plan steps to a Neo4j database to represent action feedback.
"""

from talos.executor.shim import ExecutorShim, PlanNode, ActionType

__all__ = ["ExecutorShim", "PlanNode", "ActionType"]
