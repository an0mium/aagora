"""
Nomic loop streaming via WebSocket.

Provides hook functions for emitting nomic loop events to connected clients
in real-time. Works with the existing DebateStreamServer infrastructure.

Refactored to use HookFactory for reduced boilerplate while maintaining
clear, type-safe hook definitions.
"""

from typing import Callable, Optional

from .stream import StreamEventType, StreamEvent, SyncEventEmitter


class HookFactory:
    """
    Factory for creating event emission hooks with reduced boilerplate.

    Each hook is a thin wrapper around emitter.emit() with a specific
    StreamEventType. This class reduces the repetitive code pattern:

        def on_something(arg1, arg2):
            emitter.emit(StreamEvent(
                type=StreamEventType.SOMETHING,
                data={"arg1": arg1, "arg2": arg2},
            ))

    Usage:
        factory = HookFactory(emitter)

        @factory.hook(StreamEventType.CYCLE_START)
        def on_cycle_start(cycle: int, max_cycles: int) -> dict:
            return {"cycle": cycle, "max_cycles": max_cycles}
    """

    def __init__(self, emitter: SyncEventEmitter):
        self.emitter = emitter
        self.hooks: dict[str, Callable] = {}

    def hook(
        self,
        event_type: StreamEventType,
        *,
        round_key: Optional[str] = None,
        agent_key: Optional[str] = None,
    ) -> Callable:
        """
        Decorator that registers a function as an event hook.

        The decorated function should return a dict of event data.
        Optional round_key and agent_key specify which data keys
        should be extracted for the event's round and agent fields.

        Args:
            event_type: The StreamEventType to emit
            round_key: Optional data key to use for event.round
            agent_key: Optional data key to use for event.agent
        """
        def decorator(func: Callable[..., dict]) -> Callable[..., None]:
            def wrapper(*args, **kwargs) -> None:
                data = func(*args, **kwargs)
                event = StreamEvent(
                    type=event_type,
                    data=data,
                    round=data.get(round_key, 0) if round_key else 0,
                    agent=data.get(agent_key, "") if agent_key else "",
                )
                self.emitter.emit(event)

            # Store hook with canonical name (on_xxx from function name)
            self.hooks[func.__name__] = wrapper
            return wrapper

        return decorator


def create_nomic_hooks(emitter: SyncEventEmitter) -> dict[str, Callable]:
    """
    Create hook functions for nomic loop event emission.

    These hooks should be called by NomicLoop at key points during execution.
    Events are emitted to the emitter queue for async WebSocket broadcast.

    Returns:
        dict of hook name -> callback function
    """

    def on_cycle_start(cycle_num: int, max_cycles: int, started_at: str) -> None:
        """Emit when a new nomic cycle begins."""
        emitter.emit(StreamEvent(
            type=StreamEventType.CYCLE_START,
            data={
                "cycle": cycle_num,
                "max_cycles": max_cycles,
                "started_at": started_at,
            },
        ))

    def on_cycle_end(
        cycle_num: int,
        success: bool,
        duration_seconds: float,
        outcome: str,
    ) -> None:
        """Emit when a nomic cycle completes."""
        emitter.emit(StreamEvent(
            type=StreamEventType.CYCLE_END,
            data={
                "cycle": cycle_num,
                "success": success,
                "duration_seconds": duration_seconds,
                "outcome": outcome,
            },
        ))

    def on_phase_start(
        phase: str,
        cycle: int,
        details: Optional[dict] = None,
    ) -> None:
        """Emit when a phase begins (debate, design, implement, verify, commit)."""
        emitter.emit(StreamEvent(
            type=StreamEventType.PHASE_START,
            data={
                "phase": phase,
                "cycle": cycle,
                **(details or {}),
            },
        ))

    def on_phase_end(
        phase: str,
        cycle: int,
        success: bool,
        duration_seconds: float,
        result: Optional[dict] = None,
    ) -> None:
        """Emit when a phase completes."""
        emitter.emit(StreamEvent(
            type=StreamEventType.PHASE_END,
            data={
                "phase": phase,
                "cycle": cycle,
                "success": success,
                "duration_seconds": duration_seconds,
                **(result or {}),
            },
        ))

    def on_task_start(
        task_id: str,
        description: str,
        complexity: str,
        model: str,
        total_tasks: int,
        completed_tasks: int,
    ) -> None:
        """Emit when an implementation task starts."""
        emitter.emit(StreamEvent(
            type=StreamEventType.TASK_START,
            data={
                "task_id": task_id,
                "description": description,
                "complexity": complexity,
                "model": model,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
            },
        ))

    def on_task_complete(
        task_id: str,
        success: bool,
        duration_seconds: float,
        diff_preview: str = "",
        error: Optional[str] = None,
    ) -> None:
        """Emit when an implementation task completes."""
        emitter.emit(StreamEvent(
            type=StreamEventType.TASK_COMPLETE,
            data={
                "task_id": task_id,
                "success": success,
                "duration_seconds": duration_seconds,
                "diff_preview": diff_preview,  # Full diff, no truncation
                "error": error,
            },
        ))

    def on_task_retry(
        task_id: str,
        attempt: int,
        reason: str,
        timeout: int,
    ) -> None:
        """Emit when a task is being retried."""
        emitter.emit(StreamEvent(
            type=StreamEventType.TASK_RETRY,
            data={
                "task_id": task_id,
                "attempt": attempt,
                "reason": reason,
                "timeout": timeout,
            },
        ))

    def on_verification_start(checks: list[str]) -> None:
        """Emit when verification phase begins."""
        emitter.emit(StreamEvent(
            type=StreamEventType.VERIFICATION_START,
            data={"checks": checks},
        ))

    def on_verification_result(
        check_name: str,
        passed: bool,
        message: str = "",
    ) -> None:
        """Emit result of a single verification check."""
        emitter.emit(StreamEvent(
            type=StreamEventType.VERIFICATION_RESULT,
            data={
                "check": check_name,
                "passed": passed,
                "message": message,  # Full message, no truncation
            },
        ))

    def on_commit(
        commit_hash: str,
        message: str,
        files_changed: int,
    ) -> None:
        """Emit when changes are committed."""
        emitter.emit(StreamEvent(
            type=StreamEventType.COMMIT,
            data={
                "commit_hash": commit_hash,
                "message": message,
                "files_changed": files_changed,
            },
        ))

    def on_backup_created(
        backup_name: str,
        files_count: int,
        reason: str,
    ) -> None:
        """Emit when a backup is created."""
        emitter.emit(StreamEvent(
            type=StreamEventType.BACKUP_CREATED,
            data={
                "backup_name": backup_name,
                "files_count": files_count,
                "reason": reason,
            },
        ))

    def on_backup_restored(
        backup_name: str,
        files_count: int,
        reason: str,
    ) -> None:
        """Emit when a backup is restored."""
        emitter.emit(StreamEvent(
            type=StreamEventType.BACKUP_RESTORED,
            data={
                "backup_name": backup_name,
                "files_count": files_count,
                "reason": reason,
            },
        ))

    def on_error(
        phase: str,
        message: str,
        recoverable: bool = True,
    ) -> None:
        """Emit when an error occurs."""
        emitter.emit(StreamEvent(
            type=StreamEventType.ERROR,
            data={
                "phase": phase,
                "message": message,
                "recoverable": recoverable,
            },
        ))

    def on_log_message(
        message: str,
        level: str = "info",
        phase: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> None:
        """Emit a log message for the dashboard."""
        emitter.emit(StreamEvent(
            type=StreamEventType.LOG_MESSAGE,
            data={
                "message": message,
                "level": level,
                "phase": phase,
            },
            agent=agent or "",
        ))

    def on_match_recorded(
        debate_id: str,
        participants: list[str],
        elo_changes: dict[str, float],
        domain: Optional[str] = None,
        winner: Optional[str] = None,
        loop_id: Optional[str] = None,
    ) -> None:
        """Emit when an ELO match is recorded (debate consensus feature)."""
        emitter.emit(StreamEvent(
            type=StreamEventType.MATCH_RECORDED,
            data={
                "debate_id": debate_id,
                "participants": participants,
                "elo_changes": elo_changes,
                "domain": domain,
                "winner": winner,
                "loop_id": loop_id,
            },
        ))

    def on_probe_start(
        probe_id: str,
        target_agent: str,
        probe_types: list[str],
        probes_per_type: int = 3,
    ) -> None:
        """Emit when capability probing begins for an agent."""
        emitter.emit(StreamEvent(
            type=StreamEventType.PROBE_START,
            data={
                "probe_id": probe_id,
                "target_agent": target_agent,
                "probe_types": probe_types,
                "probes_per_type": probes_per_type,
                "total_probes": len(probe_types) * probes_per_type,
            },
        ))

    def on_probe_result(
        probe_id: str,
        probe_type: str,
        passed: bool,
        severity: Optional[str] = None,
        description: str = "",
        response_time_ms: float = 0,
    ) -> None:
        """Emit individual probe result (vulnerability check)."""
        emitter.emit(StreamEvent(
            type=StreamEventType.PROBE_RESULT,
            data={
                "probe_id": probe_id,
                "probe_type": probe_type,
                "passed": passed,
                "severity": severity,
                "description": description,
                "response_time_ms": response_time_ms,
            },
        ))

    def on_probe_complete(
        report_id: str,
        target_agent: str,
        probes_run: int,
        vulnerabilities_found: int,
        vulnerability_rate: float,
        elo_penalty: float,
        by_severity: Optional[dict] = None,
    ) -> None:
        """Emit when all probes complete and report is ready."""
        emitter.emit(StreamEvent(
            type=StreamEventType.PROBE_COMPLETE,
            data={
                "report_id": report_id,
                "target_agent": target_agent,
                "probes_run": probes_run,
                "vulnerabilities_found": vulnerabilities_found,
                "vulnerability_rate": vulnerability_rate,
                "elo_penalty": elo_penalty,
                "by_severity": by_severity or {},
            },
        ))

    # Deep Audit hooks (Intensive Multi-Round Analysis)
    def on_audit_start(
        audit_id: str,
        task: str,
        agents: list[str],
        config: Optional[dict] = None,
    ) -> None:
        """Emit when deep audit session begins."""
        emitter.emit(StreamEvent(
            type=StreamEventType.AUDIT_START,
            data={
                "audit_id": audit_id,
                "task": task,
                "agents": agents,
                "config": config or {},
                "rounds": config.get("rounds", 6) if config else 6,
            },
        ))

    def on_audit_round(
        audit_id: str,
        round_num: int,
        round_name: str,
        cognitive_role: str,
        messages: list[dict],
        duration_ms: float = 0,
    ) -> None:
        """Emit when an audit round completes."""
        emitter.emit(StreamEvent(
            type=StreamEventType.AUDIT_ROUND,
            data={
                "audit_id": audit_id,
                "round": round_num,
                "name": round_name,
                "cognitive_role": cognitive_role,
                "messages": messages,
                "duration_ms": duration_ms,
            },
            round=round_num,
        ))

    def on_audit_finding(
        audit_id: str,
        category: str,
        summary: str,
        details: str,
        agents_agree: list[str],
        agents_disagree: list[str],
        confidence: float,
        severity: float = 0.0,
    ) -> None:
        """Emit when a finding is discovered during audit."""
        emitter.emit(StreamEvent(
            type=StreamEventType.AUDIT_FINDING,
            data={
                "audit_id": audit_id,
                "category": category,
                "summary": summary,
                "details": details,
                "agents_agree": agents_agree,
                "agents_disagree": agents_disagree,
                "confidence": confidence,
                "severity": severity,
            },
        ))

    def on_audit_cross_exam(
        audit_id: str,
        synthesizer: str,
        questions: list[str],
        notes: str,
    ) -> None:
        """Emit when cross-examination phase completes."""
        emitter.emit(StreamEvent(
            type=StreamEventType.AUDIT_CROSS_EXAM,
            data={
                "audit_id": audit_id,
                "synthesizer": synthesizer,
                "questions": questions,
                "notes": notes,
            },
        ))

    def on_audit_verdict(
        audit_id: str,
        task: str,
        recommendation: str,
        confidence: float,
        unanimous_issues: list[str],
        split_opinions: list[str],
        risk_areas: list[str],
        rounds_completed: int,
        total_duration_ms: float,
        agents: list[str],
        elo_adjustments: Optional[dict] = None,
    ) -> None:
        """Emit when deep audit completes with final verdict."""
        emitter.emit(StreamEvent(
            type=StreamEventType.AUDIT_VERDICT,
            data={
                "audit_id": audit_id,
                "task": task,
                "recommendation": recommendation,
                "confidence": confidence,
                "unanimous_issues": unanimous_issues,
                "split_opinions": split_opinions,
                "risk_areas": risk_areas,
                "rounds_completed": rounds_completed,
                "total_duration_ms": total_duration_ms,
                "agents": agents,
                "elo_adjustments": elo_adjustments or {},
            },
        ))

    return {
        "on_cycle_start": on_cycle_start,
        "on_cycle_end": on_cycle_end,
        "on_phase_start": on_phase_start,
        "on_phase_end": on_phase_end,
        "on_task_start": on_task_start,
        "on_task_complete": on_task_complete,
        "on_task_retry": on_task_retry,
        "on_verification_start": on_verification_start,
        "on_verification_result": on_verification_result,
        "on_commit": on_commit,
        "on_backup_created": on_backup_created,
        "on_backup_restored": on_backup_restored,
        "on_error": on_error,
        "on_log_message": on_log_message,
        "on_match_recorded": on_match_recorded,
        "on_probe_start": on_probe_start,
        "on_probe_result": on_probe_result,
        "on_probe_complete": on_probe_complete,
        "on_audit_start": on_audit_start,
        "on_audit_round": on_audit_round,
        "on_audit_finding": on_audit_finding,
        "on_audit_cross_exam": on_audit_cross_exam,
        "on_audit_verdict": on_audit_verdict,
    }
