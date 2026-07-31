from datetime import UTC, datetime

from nexo_agents.context import ContextCandidate, ContextSource, resolve_context
from nexo_contracts import FactValue

NOW = datetime(2026, 7, 30, tzinfo=UTC)


def test_confirmation_wins_over_stale_history() -> None:
    resolved = resolve_context(
        [
            ContextCandidate(
                key="municipio",
                value=FactValue(text="Gómez Palacio"),
                source=ContextSource.AUTHORIZED_HISTORY,
                observed_at=NOW,
            ),
            ContextCandidate(
                key="municipio",
                value=FactValue(text="Durango"),
                source=ContextSource.CONFIRMATION,
                observed_at=NOW,
                explicit=True,
                write_eligible=True,
            ),
        ]
    )

    assert resolved["municipio"].value.text == "Durango"
    assert resolved["municipio"].deduction is None
    assert resolved["municipio"].may_feed_write is True


def test_unconfirmed_deduction_never_feeds_a_write() -> None:
    resolved = resolve_context(
        [
            ContextCandidate(
                key="municipio",
                value=FactValue(text="Durango"),
                source=ContextSource.PROFILE,
                observed_at=NOW,
            )
        ]
    )

    assert resolved["municipio"].deduction is not None
    assert resolved["municipio"].may_feed_write is False


def test_more_recent_value_wins_within_the_same_source() -> None:
    old = datetime(2026, 1, 1, tzinfo=UTC)
    resolved = resolve_context(
        [
            ContextCandidate(
                key="afiliacion",
                value=FactValue(text="anterior"),
                source=ContextSource.AUTHORIZED_HISTORY,
                observed_at=old,
            ),
            ContextCandidate(
                key="afiliacion",
                value=FactValue(text="vigente"),
                source=ContextSource.AUTHORIZED_HISTORY,
                observed_at=NOW,
            ),
        ]
    )

    assert resolved["afiliacion"].value.text == "vigente"
