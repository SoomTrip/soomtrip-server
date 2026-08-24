CAT1_TO_THEME = {
    "A01": "nature",
    "A02": "urban",
    "A03": "activity",
    "A04": "urban",
}

# 자연(A01) 안에서 바다 세분화용 소분류(cat3) 코드
OCEAN_CAT3_CODES = [
    "A01010800",  # 폭포
    "A01010900",  # 계곡
    "A01011100",  # 해안절경
    "A01011200",  # 해수욕장
    "A01011300",  # 섬
    "A01011400",  # 항구/포구
    "A01011600",  # 등대
    "A01011700",  # 호수
    "A01011800",  # 강
]

# 바다에 접한 지역 (해안 시/도)
COASTAL_AREA_CODES = [
    "2",   # 인천
    "6",   # 부산
    "7",   # 울산
    "32",  # 강원
    "36",  # 충남
    "38",  # 전남
    "39",  # 제주
]

# 내륙 지역 (바다 접하지 않음)
INLAND_AREA_CODES = [
    "1",   # 서울
    "3",   # 대전
    "4",   # 대구
    "5",   # 광주
    "8",   # 세종
    "31",  # 경기
    "33",  # 충북
    "35",  # 경북
    "37",  # 전북
]

ALL_THEMES = ["nature", "activity", "urban", "healing", "ocean"]

THEME_TO_CAT1 = {
    "nature": ["A01"],
    "healing": ["A01"],
    "activity": ["A03"],
    "urban": ["A02", "A04"],
    "ocean": ["A01"],
}

CAT1_LABELS = {
    "A01" : "자연",
    "A02" : "문화시설",
    "A03" : "레포츠",
    "A04" : "쇼핑",
}

CAT3_LABELS = {
    "A05020900" : "카페",
}

def get_theme_from_cat3(cat1: str, cat3: str) -> str:
    """
    자연(A01) 카테고리 안에서, cat3(소분류) 코드로 바다를 세분화.
    나머지(산/계곡 등)는 nature로 처리.
    """
    if cat1 != "A01":
        return CAT1_TO_THEME.get(cat1, "nature")

    if cat3 in OCEAN_CAT3_CODES:
        return "ocean"
    return "nature"

def get_category_label(cat1: str, cat3: str = None) -> str:
    """
    cat1(대분류)/cat3(소분류) 코드를 사람이 읽을 수 있는 카테고리명으로 변환.
    카페만 소분류로 세분화하고, 나머지 음식점은 "식당"으로 통일.
    """
    if cat3 == "A05020900":
        return "카페"
    if cat1 == "A05":
        return "식당"
    return CAT1_LABELS.get(cat1, "기타")

THEME_TO_CONTENT_TYPE = {
    "nature": "12",
    "healing": "12",
    "urban": "12",
    "activity": "28",
    "ocean": "12",
}