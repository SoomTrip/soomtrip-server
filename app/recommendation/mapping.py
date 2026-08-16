CAT1_TO_THEME = {
    "A01": "nature",
    "A02": "history",
    "A03": "activity",
    "A04": "urban",
    "A05": "food",
}

# 자연(A01) 안에서 바다/숲 세분화용 소분류(cat3) 코드
OCEAN_CAT3_CODES = [
    "A01011100",  # 해안절경
    "A01011200",  # 해수욕장
    "A01011300",  # 섬
    "A01011400",  # 항구/포구
    "A01011600",  # 등대
]

FOREST_CAT3_CODES = [
    "A01010400",  # 산
    "A01010600",  # 자연휴양림
    "A01010700",  # 수목원
]

ALL_THEMES = ["nature", "history", "activity", "urban", "food", "healing", "ocean", "forest"]

THEME_TO_CAT1 = {
    "nature": ["A01"],
    "healing": ["A01"],
    "history": ["A02"],
    "activity": ["A03"],
    "urban": ["A02", "A04"],
    "food": ["A05"],
    "ocean": ["A01"],
    "forest": ["A01"],
}


def get_theme_from_cat3(cat1: str, cat3: str) -> str:
    """
    자연(A01) 카테고리 안에서, cat3(소분류) 코드로 바다/숲을 세분화.
    """
    if cat1 != "A01":
        return CAT1_TO_THEME.get(cat1, "nature")

    if cat3 in OCEAN_CAT3_CODES:
        return "ocean"
    if cat3 in FOREST_CAT3_CODES:
        return "forest"
    return "nature"

THEME_TO_CONTENT_TYPE = {
    "nature": "12",
    "healing": "12",
    "history": "12",
    "urban": "12",
    "food": "39",       # 음식점
    "activity": "28",    # 레포츠
    "ocean": "12",
    "forest": "12",
}