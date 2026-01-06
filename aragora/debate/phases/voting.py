"""
Voting phase logic extracted from Arena.

Provides utilities for:
- Vote collection and aggregation
- Semantic vote grouping (preventing artificial disagreement)
- Vote result analysis
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from aragora.core import Agent, Vote
    from aragora.debate.convergence import SimilarityBackend
    from aragora.debate.protocol import DebateProtocol

logger = logging.getLogger(__name__)


class VotingPhase:
    """Handles vote collection and aggregation logic.

    This class can be used as a mixin or standalone utility for
    managing the voting phase of a debate.
    """

    def __init__(
        self,
        protocol: "DebateProtocol",
        similarity_backend: Optional["SimilarityBackend"] = None,
    ):
        """Initialize voting phase.

        Args:
            protocol: Debate protocol with voting configuration
            similarity_backend: Optional similarity backend for vote grouping
        """
        self.protocol = protocol
        self._similarity_backend = similarity_backend

    def group_similar_votes(self, votes: list["Vote"]) -> dict[str, list[str]]:
        """Group semantically similar vote choices.

        This prevents artificial disagreement when agents vote for the
        same thing using different wording (e.g., "Vector DB" vs "Use vector database").

        Args:
            votes: List of Vote objects

        Returns:
            Dict mapping canonical choice -> list of original choices that map to it
        """
        if not self.protocol.vote_grouping or not votes:
            return {}

        # Get similarity backend (lazy load if needed)
        if self._similarity_backend is None:
            from aragora.debate.convergence import get_similarity_backend

            self._similarity_backend = get_similarity_backend("auto")
        backend = self._similarity_backend

        # Extract unique choices
        choices = list(set(v.choice for v in votes if v.choice))
        if len(choices) < 2:
            return {}

        # Build groups using union-find approach (optimized)
        groups: dict[str, list[str]] = {}  # canonical -> [choices]
        assigned: dict[str, str] = {}  # choice -> canonical

        # Track unassigned for O(n) filtering instead of O(n²) checks
        unassigned = set(choices)

        for choice in choices:
            if choice not in unassigned:
                continue

            # Start a new group with this choice as canonical
            groups[choice] = [choice]
            assigned[choice] = choice
            unassigned.remove(choice)

            # Check only remaining unassigned choices for similarity
            to_assign = []
            for other in unassigned:
                similarity = backend.compute_similarity(choice, other)
                if similarity >= self.protocol.vote_grouping_threshold:
                    groups[choice].append(other)
                    assigned[other] = choice
                    to_assign.append(other)

            # Remove newly assigned from unassigned set
            for item in to_assign:
                unassigned.remove(item)

        # Only return groups with multiple members (merges occurred)
        return {k: v for k, v in groups.items() if len(v) > 1}

    def apply_vote_grouping(
        self, votes: list["Vote"], groups: dict[str, list[str]]
    ) -> list["Vote"]:
        """Apply vote grouping to normalize vote choices.

        Args:
            votes: Original votes
            groups: Grouping map from group_similar_votes()

        Returns:
            Votes with normalized choices
        """
        if not groups:
            return votes

        # Build reverse mapping: original -> canonical
        reverse_map: dict[str, str] = {}
        for canonical, members in groups.items():
            for member in members:
                reverse_map[member] = canonical

        # Create normalized votes
        normalized = []
        for vote in votes:
            if vote.choice in reverse_map:
                # Create copy with normalized choice
                normalized.append(
                    type(vote)(
                        agent=vote.agent,
                        choice=reverse_map[vote.choice],
                        reasoning=vote.reasoning,
                        confidence=getattr(vote, "confidence", None),
                    )
                )
            else:
                normalized.append(vote)

        return normalized

    def compute_vote_distribution(
        self, votes: list["Vote"]
    ) -> dict[str, dict[str, Any]]:
        """Compute vote distribution statistics.

        Args:
            votes: List of votes

        Returns:
            Dict with choice -> {count, percentage, voters, avg_confidence}
        """
        if not votes:
            return {}

        from collections import Counter

        # Count votes per choice
        choice_counts = Counter(v.choice for v in votes if v.choice)
        total = sum(choice_counts.values())

        # Build detailed distribution
        distribution: dict[str, dict[str, Any]] = {}
        for choice, count in choice_counts.items():
            choice_votes = [v for v in votes if v.choice == choice]
            confidences = [
                v.confidence for v in choice_votes if hasattr(v, "confidence") and v.confidence is not None
            ]

            distribution[choice] = {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0,
                "voters": [v.agent for v in choice_votes],
                "avg_confidence": sum(confidences) / len(confidences) if confidences else None,
            }

        return distribution

    def determine_winner(
        self,
        votes: list["Vote"],
        require_majority: bool = False,
        min_margin: float = 0.0,
    ) -> Optional[str]:
        """Determine the winning choice from votes.

        Args:
            votes: List of votes
            require_majority: If True, winner must have >50% of votes
            min_margin: Minimum margin of victory (0-1)

        Returns:
            Winning choice, or None if no clear winner
        """
        distribution = self.compute_vote_distribution(votes)
        if not distribution:
            return None

        # Sort by count descending
        sorted_choices = sorted(
            distribution.items(), key=lambda x: x[1]["count"], reverse=True
        )

        if len(sorted_choices) == 0:
            return None

        winner, winner_stats = sorted_choices[0]

        # Check majority requirement
        if require_majority and winner_stats["percentage"] <= 50:
            return None

        # Check margin requirement
        if len(sorted_choices) > 1 and min_margin > 0:
            runner_up_pct = sorted_choices[1][1]["percentage"]
            margin = (winner_stats["percentage"] - runner_up_pct) / 100
            if margin < min_margin:
                return None

        return winner
