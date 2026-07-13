from typing import Any

from app.exceptions.domain_errors import SearchAggregatorTimeoutError


class MockSearchOrchestrator:
    """Fault-injectable search double for integration tests."""

    def __init__(self, timeout_query: str = "timeout-trigger") -> None:
        self._timeout_query = timeout_query

    def execute_query(self, query_string: str) -> dict[str, Any]:
        if query_string == self._timeout_query:
            raise SearchAggregatorTimeoutError(query_string)
        return {
            "summaryText": "Found 1 doctor near you.",
            "providers": [
                {
                    "id": "doc-77",
                    "name": "Dr. Sam",
                    "specialty": "General",
                    "distance": "1.2 miles",
                    "rating": 5.0,
                    "reviewCount": 10,
                    "nextAvailable": "Tomorrow",
                    "imageUrl": "/static/img.png",
                }
            ],
            "followUpActions": [
                {
                    "label": "Book Now",
                    "actionType": "BOOK_PROVIDER",
                    "providerId": "doc-77",
                }
            ],
        }
