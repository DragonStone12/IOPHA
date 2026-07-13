import pytest

from app.exceptions import TipNotFoundException
from app.repositories.tips_repository import InMemoryTipsRepository
from app.services.tips_service import TipsService


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
        service = TipsService(InMemoryTipsRepository())
        tip = service.get_tip("tip-002")
        assert tip.id == "tip-002"
        assert tip.title == "Arrive 15 Minutes Early"

    def test_get_tip_covers_repo_scan(self) -> None:
        # Drive both branches of InMemoryTipsRepository.get_tip_by_id so the
        # linear scan (found + absent) is fully exercised.
        repo = InMemoryTipsRepository()
        found = repo.get_tip_by_id("tip-001")
        assert found is not None
        assert found.id == "tip-001"
        assert repo.get_tip_by_id("does-not-exist") is None


class TestTipsServiceFaultInjection:
    def test_get_tip_raises_when_absent(self) -> None:
        service = TipsService(InMemoryTipsRepository())
        with pytest.raises(TipNotFoundException) as exc_info:
            service.get_tip("corrupt-id")
        assert exc_info.value.tip_id == "corrupt-id"
