def normalize_tour_item(raw: dict) -> dict:
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
        "sigungu_code": raw.get("sigungucode"),
    }