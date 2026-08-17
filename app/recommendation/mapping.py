CAT1_TO_THEME = {
    "A01": "nature",
    "A03": "activity",
    "A04": "urban",
}

# 자연(A01) 안에서 바다 세분화용 소분류(cat3) 코드
OCEAN_CAT3_CODES = [
    "A01011100",  # 해안절경
    "A01011200",  # 해수욕장
    "A01011300",  # 섬
    "A01011400",  # 항구/포구
    "A01011600",  # 등대
]

ALL_THEMES = ["nature", "activity", "urban", "healing", "ocean"]

THEME_TO_CAT1 = {
    "nature": ["A01"],
    "healing": ["A01"],
    "activity": ["A03"],
    "urban": ["A04"],
    "ocean": ["A01"],
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


THEME_TO_CONTENT_TYPE = {
    "nature": "12",
    "healing": "12",
    "urban": "12",
    "activity": "28",
    "ocean": "12",
}