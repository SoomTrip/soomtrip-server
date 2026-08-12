from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

# 카카오 로그인 사용자 정보
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    kakao_id = Column(String, unique=True, index=True, nullable=False)
    nickname = Column(String, nullable=False)
    profile_image = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 무드보드/월드컵 취향 결과(JSON 필드들을 컴럼으로 풀어놓음)
class PreferenceResult(Base):
    __tablename__ = "preference_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    primary_theme = Column(String, nullable=True)
    mood_keyword = Column(String, nullable=True)
    crowd_tolerance = Column(Integer, nullable=True)
    activity_intensity = Column(Integer, nullable=True)
    budget_level = Column(Integer, nullable=True)
    pet_friendly = Column(Boolean, default=False)
    wellness_focus = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

# 저장한 여행지 (관광공사 원본 데이터는 저장 안하고, contentId만 저장해서 나중에 실시간 재조회)
class SavedRegion(Base):
    __tablename__ = "saved_regions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    region_content_id = Column(String, nullable=False)  # TourAPI contentId
    region_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")