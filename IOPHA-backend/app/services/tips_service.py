from app.exceptions import TipNotFoundException
from app.repositories.tips_repository import TipsRepository
from app.schemas.tip import TipSchema


class TipsService:
    """Business logic for the dynamic booking tips / advice domain.

    Projects repository records into the external :class:`TipSchema` contract
    and applies presentation-level filtering (e.g. limiting the number of
    cards returned to the booking UI).
    """

    def __init__(self, repository: TipsRepository) -> None:
        self._repository = repository

    def list_tips(self, limit: int | None = None) -> list[TipSchema]:
        """Return active tips as API DTOs, optionally capped at *limit* items."""
        records = self._repository.get_active_tips()
        if records is None:
            records = []
        if limit is not None:
            records = records[:limit]
        return [
            TipSchema(
                id=record.id,
                number=record.number,
                title=record.title,
                description=record.description,
            )
            for record in records
        ]

    def get_tip(self, tip_id: str) -> TipSchema:
        """Return a single tip as an API DTO, or raise if it is absent.

        Raises :class:`TipNotFoundException` (surfaced as an RFC-7807 404)
        when no active tip matches *tip_id*.
        """
        record = self._repository.get_tip_by_id(tip_id)
        if record is None:
            raise TipNotFoundException(tip_id)
        return TipSchema(
            id=record.id,
            number=record.number,
            title=record.title,
            description=record.description,
        )


__all__ = ["TipsService"]
