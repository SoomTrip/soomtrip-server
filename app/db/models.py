import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Enum, Float, Date, UniqueConstraint
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

    # Round 1 — 풍경 (theme): ocean vs nature
    ocean_score = Column(Integer, default=0)         # 1
    nature_score = Column(Integer, default=0)        # 2
    theme_choice = Column(String, nullable=True)      # 3 — "ocean" 또는 "nature"

    # Round 2 — 이동수단 (mobility): walk_transit vs car
    walk_transit_score = Column(Integer, default=0)  # 4
    car_score = Column(Integer, default=0)             # 5
    mobility_choice = Column(String, nullable=True)    # 6 — "walk_transit" 또는 "car"

    # Round 3 — 동행자 (companion): solo vs group
    solo_score = Column(Integer, default=0)            # 7
    group_score = Column(Integer, default=0)           # 8
    companion_choice = Column(String, nullable=True)   # 9 — "solo" 또는 "group"

    # Round 4 — 여행스타일 (activity): rest vs dynamic
    rest_score = Column(Integer, default=0)             # 10
    dynamic_score = Column(Integer, default=0)          # 11
    activity_choice = Column(String, nullable=True)     # 12 — "rest" 또는 "dynamic"

    # Round 5 — 공간무드 (indoor): false(야외) vs true(실내)
    outdoor_score = Column(Integer, default=0)          # 13
    indoor_score = Column(Integer, default=0)           # 14
    indoor_choice = Column(Boolean, nullable=True)       # 15 — true(실내) 또는 false(야외)

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
    category_label = Column(String, nullable=True)     # 관광지 카테고리
    latitude = Column(Float, nullable=True)           # 지도 링크 생성용
    longitude = Column(Float, nullable=True)           # 지도 링크 생성용
    is_anchor = Column(Boolean, default=False)         # 앵커스팟(대표 관광지) 여부


    saved_region = relationship("SavedRegion", back_populates="spots")


class DiaryEntry(Base):
    """여행지에 대한 그림일기 (타임캡슐)"""
    __tablename__ = "diary_entries"

    id = Column(Integer, primary_key=True, index=True)
    saved_region_id = Column(Integer, ForeignKey("saved_regions.id"), nullable=False)  # 어느 여행지에 대한 기록인지
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)                   # 누가 작성했는지

    title = Column(Text, nullable=True)
    message = Column(Text, nullable=True)            # 일기 텍스트 내용
    image_url = Column(String, nullable=True)          # Storage에 업로드된 이미지 URL
    weather = Column(String, nullable=True)             # 날씨 (sunny, cloudy, rainy, snowy)

    date = Column(Date, nullable=False)      # 여행일

    is_public = Column(Boolean, default=True)             # 다음 방문자에게 공개할지 여부

    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 이 일기를 등록한 시각(자동)

    user = relationship("User")
    saved_region = relationship("SavedRegion")

class Stamp(Base):
    """일기를 작성한 여행지에 부여되는 도장"""
    __tablename__ = "stamps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    saved_region_id = Column(Integer, ForeignKey("saved_regions.id"), nullable=False)
    stamp_asset_key = Column(String, nullable=False)   # 예: "stamp1", "stamp2"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    saved_region = relationship("SavedRegion")

    __table_args__ = (
        UniqueConstraint("user_id", "saved_region_id", name="uq_user_saved_region_stamp"),
    )

class RouteEntry(Base):
    """사용자가 확정한 동선(경로)의 한 스텝. 
    다시 저장하면 기존 것은 삭제되고 새로운 것으로 대체됨(API 로직에서 처리)."""
    __tablename__ = "route_entries"

    id = Column(Integer, primary_key=True, index=True)
    saved_region_id = Column(Integer, ForeignKey("saved_regions.id"), nullable=False)
    saved_region_spot_id = Column(Integer, ForeignKey("saved_region_spots.id"), nullable=False)

    visit_day = Column(Integer, nullable=False)             # 몇 일차인지
    visit_order = Column(Integer, nullable=False)             # 그 날 안에서 몇 번째 방문인지

    distance_from_prev_km = Column(Float, nullable=True)             # 이전 지점부터 여기까지 거리
    duration_from_prev_minutes = Column(Integer, nullable=True)      # 이전 지점부터 여기까지 시간
    mobility_choice = Column(String, nullable=True)                   # 이 동선을 짤 때 이동수단

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    saved_region = relationship("SavedRegion")
    saved_region_spot = relationship("SavedRegionSpot")