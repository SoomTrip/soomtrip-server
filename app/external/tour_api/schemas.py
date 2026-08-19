def normalize_tour_item(raw: dict) -> dict:
    l_dong_regn_cd = raw.get("lDongRegnCd", "")
    l_dong_signgu_cd = raw.get("lDongSignguCd", "")
    
    # 법정동 통계청 코드 조합 (예: "11" + "500" -> "11500")
    stat_sigungu_code = None
    if l_dong_regn_cd and l_dong_signgu_cd:
        stat_sigungu_code = l_dong_regn_cd + l_dong_signgu_cd.zfill(3)

    return {
        "id": raw.get("contentid"),
        "content_type_id": raw.get("contenttypeid"),
        "name": raw.get("title"),
        "address": raw.get("addr1", "") + " " + raw.get("addr2", ""),
        "latitude": float(raw["mapy"]) if raw.get("mapy") else None,
        "longitude": float(raw["mapx"]) if raw.get("mapx") else None,
        "image_url": raw.get("firstimage") or raw.get("firstimage2"),
        "cat1": raw.get("cat1"),
        "cat2": raw.get("cat2"),
        "cat3": raw.get("cat3"),
        "area_code": raw.get("areacode"),
        "sigungu_code": raw.get("sigungucode"),           # TourAPI 자체 코드 (기존, 병합 로직에서 계속 사용)
        "stat_area_code": l_dong_regn_cd,                  # 통계청 광역코드
        "stat_sigungu_code": stat_sigungu_code,             # 통계청 시군구코드 (수요강도 API 연동용)
    }