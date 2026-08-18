from app.db.session import Base, engine
from app.db.models import User, Friend, PreferenceResult, SavedRegion

Base.metadata.create_all(bind=engine)
print("테이블 생성 완료")