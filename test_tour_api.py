from app.external.tour_api.client import get_location_based_list
from app.external.tour_api.schemas import normalize_tour_item

# 갈산공원 근처 3km 이내 관광지
items = get_location_based_list(map_x=126.8684105358, map_y=37.5061176314, radius=3000)
for item in items:
    print(normalize_tour_item(item))