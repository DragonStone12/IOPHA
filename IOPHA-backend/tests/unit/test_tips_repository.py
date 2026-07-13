from app.repositories.tips_repository import InMemoryTipsRepository, TipRecord


class TestInMemoryTipsRepository:
    """Unit tests for the in-memory tips repository stand-in."""

    def test_get_tip_by_id_returns_record_when_present(self) -> None:
        repo = InMemoryTipsRepository()
        found = repo.get_tip_by_id("tip-001")
        assert found is not None
        assert found.id == "tip-001"
        assert isinstance(found, TipRecord)

    def test_get_tip_by_id_returns_none_when_absent(self) -> None:
        repo = InMemoryTipsRepository()
        assert repo.get_tip_by_id("does-not-exist") is None

    def test_get_active_tips_returns_ordered_list(self) -> None:
        repo = InMemoryTipsRepository()
        tips = repo.get_active_tips()
        assert len(tips) > 0
        assert all(isinstance(tip, TipRecord) for tip in tips)
        # Derive the expected ordering from the number of seeded tips instead of
        # hardcoding the seed-data count, so this stays correct if seeds change.
        assert [tip.number for tip in tips] == list(range(1, len(tips) + 1))

    def test_get_active_tips_returns_shallow_copy(self) -> None:
        repo = InMemoryTipsRepository()
        tips_a = repo.get_active_tips()
        tips_b = repo.get_active_tips()
        assert tips_a is not tips_b
        assert tips_a[0] is tips_b[0]
