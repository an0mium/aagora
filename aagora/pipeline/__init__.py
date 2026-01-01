"""
Pipeline module for aagora - Decision-to-PR generation.

Transforms debate outcomes into actionable development artifacts:
- DecisionMemo: Summary of debate conclusions
- RiskRegister: Identified risks and mitigations
- TestPlan: Verification strategy
- PatchPlan: Implementation steps
"""

from aagora.pipeline.pr_generator import PRGenerator, DecisionMemo, PatchPlan
from aagora.pipeline.risk_register import RiskRegister, Risk
from aagora.pipeline.test_plan import TestPlan, TestCase

__all__ = [
    "PRGenerator",
    "DecisionMemo",
    "PatchPlan",
    "RiskRegister",
    "Risk",
    "TestPlan",
    "TestCase",
]
