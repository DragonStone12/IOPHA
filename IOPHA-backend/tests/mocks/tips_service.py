from typing import Callable

from app.repositories.tips_repository import TipRecord, TipsRepository


class MockTipsRepository(TipsRepository):
    """Fault-injectable tips repository for isolated error-handling tests.

    Implements the :class:`TipsRepository` interface with a configurable
    set of seeded tips and a set of ids that should resolve to "absent"
    so the service raises :class:`TipNotFoundException` without touching
    any live datastore.
    """

    def __init__(
        self,
        tips: list[TipRecord] | None = None,
        missing_ids: set[str] | None = None,
        raise_on_get_tip: Callable[[str], Exception] | None = None,
    ) -> None:
        self._tips = (
            tips
            if tips is not None
            else [
                TipRecord(
                    id="tip-001",
                    number=1,
                    title="Hydrate Early",
                    description="Drink plenty of water throughout the day.",
                ),
                TipRecord(
                    id="tip-002",
                    number=2,
                    title="Check In",
                    description="Arrive 15 minutes early.",
                ),
            ]
        )
        self._missing_ids = missing_ids or set()
        self._raise_on_get_tip = raise_on_get_tip

    def get_active_tips(self) -> list[TipRecord]:
        return list(self._tips)

    def get_tip_by_id(self, tip_id: str) -> TipRecord | None:
        if self._raise_on_get_tip is not None:
            raise self._raise_on_get_tip(tip_id)
        if tip_id in self._missing_ids:
            return None
        for tip in self._tips:
            if tip.id == tip_id:
                return tip
        return None
