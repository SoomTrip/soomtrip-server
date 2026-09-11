from app.db.session import SessionLocal
from app.services.route_cleanup_service import cleanup_expired_route_data


def main():
    db = SessionLocal()

    try:
        count = cleanup_expired_route_data(db)
        print(f"Cleaned expired route data: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()