"""Shared seed records for the in-memory repository stand-ins.

This module is the single source of truth for the out-of-the-box demo data
used until a real datastore is wired. Both ``InMemoryCalendarRepository`` and
``InMemoryProviderRepository`` intentionally start pre-populated with these
records so the availability and booking endpoints return realistic data
without external state. Keeping the seed here guarantees the two repositories
cannot silently diverge.
"""

from dataclasses import replace

from app.schemas import ProviderRecord

_SEED_PROVIDERS: tuple[ProviderRecord, ...] = (
    ProviderRecord(
        id="prov-123",
        name="Dr. Emily Chen, MD",
        specialty="Cardiology",
        distance="1.8 miles",
        rating=4.9,
        reviewCount=120,
        nextAvailable="Today, 3:30 PM",
        imageUrl="https://cdn.example.com/emily.jpg",
        facility="Northside Medical Center",
        db_primary_key=42,
    ),
)


def seed_providers() -> dict[str, ProviderRecord]:
    """Return a fresh dict of seed provider records keyed by provider id.

    Each call returns new ``ProviderRecord`` copies so repositories can mutate
    their own store without affecting other consumers of the seed data.
    """
    return {provider.id: replace(provider) for provider in _SEED_PROVIDERS}


__all__ = ["seed_providers"]
