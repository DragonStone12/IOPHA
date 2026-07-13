import pytest

from app.exceptions import TipNotFoundException
from app.repositories.tips_repository import InMemoryTipsRepository, TipRecord
from app.services.tips_service import TipsService
from tests.mocks.tips_service import MockTipsRepository


class TestTipsServiceHappyPath:
    """Unit tests for the tips service against an in-memory repository.

    These exercise the service layer directly (no HTTP transport) so the
    presentation/limit logic and the ``get_tip_by_id`` repository scan
    are covered in isolation.
    """

    def test_list_tips_returns_schemas_in_number_order(self) -> None:
        service = TipsService(InMemoryTipsRepository())
        tips = service.list_tips()
        assert len(tips) == 3
        assert all(tip.number >= 1 for tip in tips)
        assert [tip.number for tip in tips] == sorted(tip.number for tip in tips)

    def test_list_tips_caps_with_limit(self) -> None:
        service = TipsService(InMemoryTipsRepository())
        tips = service.list_tips(limit=1)
        assert len(tips) == 1

    def test_get_tip_returns_schema(self) -> None:
        expected = TipRecord(
            id="tip-002",
            number=2,
            title="Arrive 15 Minutes Early",
            description="Buffer for check-in paperwork.",
        )
        repo = MockTipsRepository(tips=[expected])
        service = TipsService(repo)
        tip = service.get_tip("tip-002")
        assert tip.id == expected.id
        assert tip.number == expected.number
        assert tip.title == expected.title
        assert tip.description == expected.description


class TestTipsServiceFaultInjection:
    def test_get_tip_raises_when_absent(self) -> None:
        service = TipsService(InMemoryTipsRepository())
        with pytest.raises(TipNotFoundException) as exc_info:
            service.get_tip("corrupt-id")
        assert exc_info.value.tip_id == "corrupt-id"
