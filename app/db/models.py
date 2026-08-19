import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum

# 카카오 로그인 사용자 정보
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    kakao_id = Column(String, unique=True, index=True, nullable=False)  # 카카오 고유 회원번호
    nickname = Column(String, nullable=False)  # 숨트립 내 표시 닉네임 (카카오 닉네임으로 최초 생성, 이후 수정 가능, 중복 허용)
    user_code = Column(String, unique=True, index=True, nullable=False, default=lambda: uuid.uuid4().hex[:10]) # 친구추가용 고유 코드
    profile_image = Column(String, nullable=True)  # 프로필 사진 URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FriendStatus(str, enum.Enum):
    PENDING = "PENDING" # 요청 보냄, 아직 상대 수락 안함
    ACCEPTED = "ACCEPTED" # 수락 완료, 친구관계
    REJECTED = "REJECTED" # 거절됨


# 친구 정보
class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True) # 친구 관계 고유 번호
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False) # 친구 요청을 보낸 user
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False) # 친구 요청을 받은 user
    status = Column(Enum(FriendStatus), default=FriendStatus.PENDING, nullable=False) # 요청 상태
    created_at = Column(DateTime(timezone=True), server_default=func.now()) #요청 보낸 시각
    accepted_at = Column(DateTime(timezone=True), nullable=True) # 수락되 시각 (수락 전 none)

    requester = relationship("User", foreign_keys=[requester_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


# 월드컵 취향 결과 (선택할 때마다 태그별 점수가 누적됨, 정규화 전 원본 점수)
class PreferenceResult(Base):
    __tablename__ = "preference_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 태그별 누적 점수
    nature_score = Column(Integer, default=0)
    activity_score = Column(Integer, default=0)
    healing_score = Column(Integer, default=0)
    urban_score = Column(Integer, default=0)
    ocean_score = Column(Integer, default=0)   # 바다

    # 여행 조건
    budget_level = Column(Integer, nullable=True)         # 1(가성비) ~ 3(플렉스)
    transport = Column(String, nullable=True)              # "CAR" 또는 "PUBLIC_TRANSIT"
    activity_intensity = Column(Integer, nullable=True)    # 1(완전휴식) ~ 5(완전액티비티)
    departure_area_code = Column(String, nullable=True)    # 출발/희망 지역 (TourAPI 지역코드)

    # 특수 조건 (추가 구현시 활용 예정)
    pet_friendly = Column(Boolean, default=False)          # 반려동물 동반 여부
    wellness_focus = Column(Boolean, default=False)        # 웰니스/힐링 목적 여부

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class SavedRegion(Base):
    """사용자가 저장(찜)한 여행지 (지역 단위, 여러 관광지를 포함)"""
    __tablename__ = "saved_regions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    region_name = Column(String, nullable=False)   # 예: "양양 현북면"
    score = Column(Integer, nullable=True)          # 추천 당시 점수 (참고용, 선택사항)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    spots = relationship("SavedRegionSpot", back_populates="saved_region", cascade="all, delete-orphan")


class SavedRegionSpot(Base):
    """저장된 여행지에 포함된 관광지 하나 (앵커스팟 포함 전체)"""
    __tablename__ = "saved_region_spots"

    id = Column(Integer, primary_key=True, index=True)
    saved_region_id = Column(Integer, ForeignKey("saved_regions.id"), nullable=False)
    content_id = Column(String, nullable=False)      # TourAPI contentId (실시간 재조회용)
    name = Column(String, nullable=False)             # 화면 표시용 이름 (캐시 목적)
    is_anchor = Column(Boolean, default=False)         # 앵커스팟(대표 관광지) 여부

    saved_region = relationship("SavedRegion", back_populates="spots")