from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import RouteEntry


ROUTE_DATA_TTL = timedelta(hours=24)


def cleanup_expired_route_data(db: Session) -> int:
    cutoff = datetime.now(timezone.utc) - ROUTE_DATA_TTL

    updated_count = (
        db.query(RouteEntry)
        .filter(
            RouteEntry.mobility_choice == "walk_transit",
            RouteEntry.created_at < cutoff,
            (
                (RouteEntry.distance_from_prev_km.isnot(None))
                | (RouteEntry.duration_from_prev_minutes.isnot(None))
            ),
        )
        .update(
            {
                RouteEntry.distance_from_prev_km: None,
                RouteEntry.duration_from_prev_minutes: None,
            },
            synchronize_session=False,
        )
    )

    db.commit()
    return updated_count