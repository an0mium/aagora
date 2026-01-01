"""
Hybrid multi-model executor.

Updated routing based on empirical performance data (Dec 2025):
- Claude: ALL implementation tasks (37% faster than alternatives, best code quality)
- Codex: Code review / QA after implementation (high quality review, latency-tolerant)
- Gemini: Planning only (handled by planner.py, leverages 1M context window)

Research sources:
- Claude completed projects in 1h17m vs Gemini's 2h2m (37% faster)
- Codex has known latency issues (5-20 min for simple tasks per GitHub issues)
- Claude produces "production-ready codebase with organized folders"
- Codex excels at review/QA where latency isn't critical
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

from aragora.agents.cli_agents import ClaudeAgent, CodexAgent

from .types import ImplementTask, TaskResult


TASK_PROMPT_TEMPLATE = """Implement this task in the codebase:

## Task
{description}

## Files to Create/Modify
{files}

## Repository
Working directory: {repo_path}

## Instructions

1. Create or modify the files listed above
2. Follow existing code style and patterns
3. Include docstrings and type hints
4. Make only the changes necessary for this task
5. Do not break existing functionality

IMPORTANT: Only make changes that are safe and reversible.
"""


class HybridExecutor:
    """
    Executes implementation tasks using Claude, with optional Codex review.

    Updated routing strategy (Dec 2025):
    - ALL tasks: Claude (fastest, best quality for implementation)
    - Post-implementation: Codex review (optional QA phase)

    Rationale:
    - Codex has severe latency issues (GitHub #5149, #1811, #6990)
    - Claude is 37% faster and produces more organized code
    - Codex quality shines in review mode where latency is acceptable
    """

    def __init__(
        self,
        repo_path: Path,
        claude_timeout: int = 600,
        codex_timeout: int = 300,
    ):
        self.repo_path = repo_path

        # Initialize agents lazily (created on first use)
        self._claude: Optional[ClaudeAgent] = None
        self._codex: Optional[CodexAgent] = None

        self.claude_timeout = claude_timeout
        self.codex_timeout = codex_timeout

    @property
    def claude(self) -> ClaudeAgent:
        if self._claude is None:
            self._claude = ClaudeAgent(
                name="claude-implementer",
                model="claude",
                role="implementer",
                timeout=self.claude_timeout,
            )
            self._claude.system_prompt = """You are implementing code changes in a repository.
Be precise, follow existing patterns, and make only necessary changes.
Include proper type hints and docstrings."""
        return self._claude

    @property
    def codex(self) -> CodexAgent:
        if self._codex is None:
            self._codex = CodexAgent(
                name="codex-specialist",
                model="o3",
                role="implementer",
                timeout=self.codex_timeout,
            )
            self._codex.system_prompt = """You are implementing a focused code change.
Make only the changes specified. Follow existing code style."""
        return self._codex

    def _select_agent(self, complexity: str):
        """Select the appropriate agent based on task complexity.

        Updated Dec 2025: Always use Claude for implementation.
        Codex latency issues make it unsuitable for interactive implementation.
        Codex is now used only for post-implementation review.
        """
        # Always use Claude for implementation (fastest, best quality)
        # Complexity only affects timeout expectations
        return self.claude, "claude"

    def _build_prompt(self, task: ImplementTask) -> str:
        """Build the implementation prompt for a task."""
        files_str = "\n".join(f"- {f}" for f in task.files) if task.files else "- (determine from description)"

        return TASK_PROMPT_TEMPLATE.format(
            description=task.description,
            files=files_str,
            repo_path=str(self.repo_path),
        )

    def _get_git_diff(self) -> str:
        """Get the current git diff."""
        try:
            result = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout
        except Exception:
            return ""

    async def execute_task(self, task: ImplementTask) -> TaskResult:
        """
        Execute a single implementation task.

        Args:
            task: The task to execute

        Returns:
            TaskResult with success status and diff
        """
        agent, model_name = self._select_agent(task.complexity)
        prompt = self._build_prompt(task)

        print(f"  Executing [{task.complexity}] {task.id} with {model_name}...")
        start_time = time.time()

        try:
            # Execute with the selected agent
            await agent.generate(prompt, context=[])

            # Get the diff to see what changed
            diff = self._get_git_diff()
            duration = time.time() - start_time

            print(f"    Completed in {duration:.1f}s")
            if diff:
                print(f"    Changes:\n{diff[:200]}...")

            return TaskResult(
                task_id=task.id,
                success=True,
                diff=diff,
                model_used=model_name,
                duration_seconds=duration,
            )

        except TimeoutError as e:
            duration = time.time() - start_time
            print(f"    Timeout after {duration:.1f}s")
            return TaskResult(
                task_id=task.id,
                success=False,
                error=f"Timeout: {e}",
                model_used=model_name,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"    Error: {e}")
            return TaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                model_used=model_name,
                duration_seconds=duration,
            )

    async def execute_plan(
        self,
        tasks: list[ImplementTask],
        completed: set[str],
        on_task_complete=None,
    ) -> list[TaskResult]:
        """
        Execute all tasks in a plan, respecting dependencies.

        Args:
            tasks: List of tasks to execute
            completed: Set of already-completed task IDs
            on_task_complete: Optional callback after each task

        Returns:
            List of TaskResults for executed tasks
        """
        results = []

        for task in tasks:
            # Skip already completed
            if task.id in completed:
                continue

            # Check dependencies
            deps_met = all(dep in completed for dep in task.dependencies)
            if not deps_met:
                print(f"  Skipping {task.id} - dependencies not met")
                continue

            # Execute
            result = await self.execute_task(task)
            results.append(result)

            if result.success:
                completed.add(task.id)
                if on_task_complete:
                    on_task_complete(task.id, result)
            else:
                # Stop on first failure
                print(f"  Stopping execution due to failure in {task.id}")
                break

        return results

    async def review_with_codex(self, diff: str, timeout: int = 600) -> dict:
        """
        Run Codex code review on implemented changes.

        Codex is slow (~5-20min) but produces high-quality review.
        Use this as a QA step after Claude implementation.

        Args:
            diff: The git diff to review
            timeout: Max time to wait (default 10 min)

        Returns:
            dict with 'approved', 'issues', and 'suggestions'
        """
        if not diff.strip():
            return {"approved": True, "issues": [], "suggestions": []}

        review_prompt = f"""Review this code change for quality and safety issues.

## Git Diff
```
{diff}
```

## Review Checklist
1. Are there any bugs or logic errors?
2. Are there security vulnerabilities (injection, XSS, etc.)?
3. Does the code follow consistent style?
4. Are there missing error handlers or edge cases?
5. Is there unnecessary complexity that could be simplified?

## Response Format
Provide your review as:
- APPROVED: yes/no
- ISSUES: List any problems that MUST be fixed
- SUGGESTIONS: List any improvements that would be nice

Be concise and actionable."""

        print("  Running Codex code review (this may take several minutes)...")
        start_time = time.time()

        try:
            # Use codex with extended timeout for review
            self._codex = CodexAgent(
                name="codex-reviewer",
                model="o3",
                role="reviewer",
                timeout=timeout,
            )
            self._codex.system_prompt = """You are a senior code reviewer.
Focus on correctness, security, and maintainability.
Be constructive but thorough."""

            response = await self._codex.generate(review_prompt, context=[])
            duration = time.time() - start_time

            print(f"    Review completed in {duration:.1f}s")

            # Parse response (basic parsing)
            response_lower = response.lower() if response else ""
            approved = "approved: yes" in response_lower or "approved:yes" in response_lower

            return {
                "approved": approved,
                "review": response,
                "duration_seconds": duration,
                "model": "codex-o3",
            }

        except Exception as e:
            duration = time.time() - start_time
            print(f"    Review failed after {duration:.1f}s: {e}")
            return {
                "approved": None,
                "error": str(e),
                "duration_seconds": duration,
            }
