from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderRecord:
    """Internal relational domain shape returned by the provider repository.

    This is the raw datastore representation and MUST NOT be serialized
    directly to clients. Note ``db_primary_key`` is a structural identifier
    used only for persistence; it is deliberately dropped by the mapping
    layer so it never crosses the API boundary.
    """

    id: str
    name: str
    specialty: str
    distance: str
    rating: float
    reviewCount: int
    nextAvailable: str
    imageUrl: Optional[str] = None
    facility: Optional[str] = None
    db_primary_key: int = 0
