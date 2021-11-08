import pymongo
from repositories.connectors import MongoDBConnector


def find_location_to_geopoint(client: pymongo.MongoClient, lat: float, lon: float) -> dict:
    """
    위도/경도를 통해서 충돌되는 위치 정보에 대한 주소를 반환한다

    :param client:
    :param lat:
    :param lon:
    :return:
    """
    data = client.find_one({
        "geometry": {
            "$geoIntersects": {
                "$geometry": {
                    "type": 'Point',
                    "coordinates": [lon, lat]
                }
            }
        }
    }, {
        '_id': 0,
        'Sido': 1,
        'Sigun': 1,
        'Gu': 1,
        'Dong': 1,
        'Address': 1,
    })

    if data:
        return data
    else:
        # geoIntersects 로 검색되지 않는다면, 좌표와 가장 근접한 위치를 반환한다
        data = client.find_one({
            "geometry": {
                "$geoNear": {
                    "$geometry": {
                        "type": 'Point',
                        "coordinates": [lon, lat],
                    },
                }
            }
        }, {
            '_id': 0,
            'Sido': 1,
            'Sigun': 1,
            'Gu': 1,
            'Dong': 1,
            'Address': 1,
        })

        return data


mdb_conn = MongoDBConnector().conn()
conn = mdb_conn["Locations"]["HangJeongDong"]
exam_lon = 127.0016985
exam_lat = 37.5642135

results = find_location_to_geopoint(client=conn, lat=exam_lat, lon=exam_lon)
print(results)
### Output
# {'Sido': '서울특별시', 'Sigun': '서울특별시', 'Gu': '중구', 'Dong': '광희동', 'Address': '서울특별시 중구 광희동'}
