import os
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("AI_API_KEY"))


def get_clover_emoji() -> str:
    """
    75% 확률로 세잎클로버(☘️), 25% 확률로 네잎클로버(🍀, 행운)를 반환.
    """
    THREE_LEAF = "☘️"
    FOUR_LEAF = "🍀"
    return random.choices([THREE_LEAF, FOUR_LEAF], weights=[70, 30])[0]


def get_preference_description(theme_weights: dict) -> str:
    """
    상위 1~2개 테마를 조합해서 사용자 성향을 더 풍부하게 설명.
    두 번째 테마가 첫 번째와 비슷한 비중이면 함께 언급.
    """
    theme_desc_map = {
        "ocean": "탁 트인 풍경과 시원한 바람을 좋아하는",
        "nature": "자연 속에서 편안함을 느끼는",
        "activity": "가만히 있기보다 활동적으로 움직이는 걸 즐기는",
        "urban": "정돈된 분위기와 실내 공간을 편안해하는",
        "healing": "복잡한 일상에서 벗어나 여유롭게 쉬고 싶은",
    }

    sorted_themes = sorted(theme_weights.items(), key=lambda x: x[1], reverse=True)
    if not sorted_themes or sorted_themes[0][1] == 0:
        return "새로운 여행을 원하는"

    top_theme, top_score = sorted_themes[0]
    top_desc = theme_desc_map.get(top_theme, "새로운 여행을 원하는")

    if len(sorted_themes) > 1:
        second_theme, second_score = sorted_themes[1]
        if second_score > 0 and second_score >= top_score * 0.6:
            second_desc = theme_desc_map.get(second_theme, "")
            if second_desc:
                return f"{top_desc} 동시에 {second_desc}"

    return top_desc


def get_destination_characteristics(score_detail: dict) -> str:
    """
    score_detail(스코어링 세부 점수)을 바탕으로,
    지명 없이 여행지의 실제 특성을 설명하는 힌트를 생성한다.
    """
    characteristics = []

    crowd_score = score_detail.get("crowd_score", 50)
    if crowd_score >= 65:
        characteristics.append("사람들의 발길이 드문 한적한 곳")
    elif crowd_score <= 35:
        characteristics.append("적당히 활기가 느껴지는 곳")

    diversity_score = score_detail.get("diversity_score", 50)
    if diversity_score >= 65:
        characteristics.append("주변에 둘러볼 것이 풍부한 곳")
    elif diversity_score <= 30:
        characteristics.append("소박하고 아늑한 곳")

    indoor_match_score = score_detail.get("indoor_match_score", 50)
    if indoor_match_score >= 80:
        characteristics.append("찾던 분위기와 꼭 맞는 공간")

    if not characteristics:
        return ""

    return ", ".join(characteristics)


def generate_one_line_review(
    region_name: str,
    theme_weights: dict,
    score_detail: dict,
) -> str:
    """
    추천된 여행지에 대한 한줄평을 AI로 생성.
    구체적인 장소명은 언급하지 않되, 사용자의 취향과 실제 여행지의 특성
    (혼잡도, 다양성 등)을 함께 반영해 더 정확하고 풍부한 문구를 만든다.
    마지막에는 클로버 이모지를 확률적으로 붙인다(코드에서 직접 제어).
    """
    preference_desc = get_preference_description(theme_weights)
    destination_desc = get_destination_characteristics(score_detail)

    destination_hint_line = (
        f"이 여행지의 실제 특징: {destination_desc}"
        if destination_desc
        else "이 여행지의 특징: 특별히 두드러지는 특징 없이 무난함"
    )

    prompt = f"""
당신은 숨은 여행 추천 앱 '숨트립'의 카피라이터입니다.
사용자가 월드컵(취향 테스트)에서 선택한 결과와, 실제로 추천된 여행지의 특징을
함께 반영해서 자연스러운 한 줄 문구를 만들어주세요.

사용자 성향 힌트: {preference_desc} 사람
{destination_hint_line}

문구 스타일 예시 (참고만 하고 그대로 베끼지 마세요):
- "분주한 일정보다 느긋한 여유에 마음이 가는 당신에게, 이곳을 추천해요!"
- "익숙한 일상에서 살짝 벗어나 새로운 분위기를 만나고 싶다면, 이곳은 어때요?"
- "화려함보다 편안함, 북적임보다 한적함을 고른 당신에게 잘 어울리는 여행지예요!"
- "이것저것 채우기보다 마음 가는 대로 머물고 싶은 이번 여행에 추천해요!"
- "조용히 쉬는 것도 좋지만 새로운 즐거움도 놓치기 싫은 당신에게, 이곳을 추천해요!"

작성 조건:
- 완전한 문장으로 작성할 것 (구절이 아니라 자연스러운 문장체)
- "당신에게", "~어때요?", "~추천해요!" 같은 다정하게 말을 거는 톤을 사용할 것
- 구체적인 지명, 장소 이름, 특정 활동(예: 카페, 등산 등)은 절대 언급하지 말 것
- 사용자의 취향뿐 아니라, 위에 제공된 "여행지의 실제 특징"도 자연스럽게 녹여낼 것
  (단, 특징을 그대로 나열하지 말고 문장에 은은하게 녹여낼 것)
- 20~35자 내외
- 위 5개 예시와는 다른, 새로운 표현으로 작성할 것
- 물음표 또는 느낌표로 자연스럽게 끝낼 것
- 이모지는 포함하지 말 것

출력은 반드시 문구 하나만, 다른 설명이나 인사말 없이 작성하세요.

문구의 길이는 이후 보내줄 예시보다 무조건 짧거나 같게 만들어야해요.
예시는 "활기 넘치는 경험을 원한다면, 이곳이 당신의 다음 여행지에 잘 어울려요!🍀" 입니다.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.8,
        )
        text = response.choices[0].message.content.strip()
        emoji = get_clover_emoji()
        return f"{text}{emoji}"
    except Exception as e:
        print(f"[generate_one_line_review] AI 호출 실패: {e}")
        return f"당신의 취향에 꼭 맞는 여행지를 찾았어요!{get_clover_emoji()}"