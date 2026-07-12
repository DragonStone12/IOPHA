from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TipRecord:
    """Internal tips-store representation before projection into the API DTO.

    This is the raw repository shape. The service layer projects it into the
    external :class:`TipSchema` contract, dropping any structural identifiers
    that must never cross the API boundary.
    """

    id: str
    number: int
    title: str
    description: str


class TipsRepository(ABC):
    """Persistence boundary for dynamic booking tip / advice lookups."""

    @abstractmethod
    def get_active_tips(self) -> list[TipRecord]:
        """Return the ordered set of active tips (may be empty)."""


class InMemoryTipsRepository(TipsRepository):
    """Default no-database stand-in used until a real datastore is wired.

    Seeds a deterministic set of onboarding/booking advice cards so the tips
    endpoint returns realistic data without any external state.
    """

    def __init__(self) -> None:
        self._tips: list[TipRecord] = [
            TipRecord(
                id="tip-001",
                number=1,
                title="Hydrate Early",
                description=(
                    "Drink plenty of water throughout the day to stay ahead of "
                    "dehydration before your appointment."
                ),
            ),
            TipRecord(
                id="tip-002",
                number=2,
                title="Arrive 15 Minutes Early",
                description=(
                    "Give yourself a buffer to complete check-in paperwork and "
                    "settle in before your scheduled time."
                ),
            ),
            TipRecord(
                id="tip-003",
                number=3,
                title="Bring Your Medication List",
                description=(
                    "A current list of medications and dosages helps your "
                    "provider make safe, informed recommendations."
                ),
            ),
        ]

    def get_active_tips(self) -> list[TipRecord]:
        # Return a shallow copy so callers cannot mutate the seeded store.
        return list(self._tips)


__all__ = [
    "InMemoryTipsRepository",
    "TipRecord",
    "TipsRepository",
]
