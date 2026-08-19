# recreate_saved_regions.py
from app.db.session import Base, engine
from app.db.models import SavedRegion, SavedRegionSpot

# 기존 saved_regions 테이블 삭제
SavedRegion.__table__.drop(engine, checkfirst=True)

# 새 구조로 재생성 (saved_regions + saved_region_spots 둘 다 생성됨)
Base.metadata.create_all(bind=engine)
print("saved_regions, saved_region_spots 테이블 재생성 완료")