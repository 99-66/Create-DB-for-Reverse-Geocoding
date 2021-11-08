# Reverse Geocoding 을 위한 Database 만들기

위도, 경도를 주소로 직접 변환하기 위한 행정동 Database를 만든다

MongoDB 와 Python 을 통해 reverse geocoding을 위한 database를 만들어보자
```
사실 처음에는 외부에서 제공하는 API를 사용하려 했으나 제약이 심하여 많은 양을 변환하기에는 무리가 있었다
  - API Request Count limit
  - API를 통해 변환된 주소는 별도 DB 저장불가 등
```

## Insert Dataset
DB에 들어가야 할 행정동 경계 파일은 [https://github.com/vuski/admdongkor](https://github.com/vuski/admdongkor) 에 있는 파일을 사용한다

파일을 MongoDB에 insert하기 위한 전처리가 필요하다
> utils/address.py
```python
def split_sido_sggnm(df):
    """
    시군구 명칭과 시도 명칭에서 각각 '시', '군' 명칭을 분리하여 반환한다

    :param df:
    :return:
    """
    if df['sggnm'] == '시흥시':
        return df['sggnm']

    if df['sidonm'].endswith('시'):
        return df['sidonm']
    elif '시' in df['sggnm']:
        return f"{df['sggnm'].split('시')[0]}시"
    else:
        return df['sggnm']
```
```python
def split_sggnm_gu(df):
    """
    시군구 명칭에서 '구' 명칭을 분리하여 반환한다

    :param df:
    :return:
    """
    if df['sggnm'] == '시흥시':
        return None

    if '시' in df['sggnm']:
        return f"{df['sggnm'].split('시')[1]}"
    elif df['sggnm'].endswith('구'):
        return df['sggnm']
    else:
        return ''
```
```python
def make_full_address(df):
    """
    시군, 구, 동 명칭을 합하여 원본 주소를 생성하여 반환한다

    :param df:
    :return:
    """
    if df['Gu']:
        if df['Sido'] != df['Sigun']:
            address = f'{df["Sido"]} {df["Sigun"]} {df["Gu"]} {df["Dong"]}'
        else:
            address = f'{df["Sigun"]} {df["Gu"]} {df["Dong"]}'
    else:
        if df['Sido'] != df['Sigun']:
            address = f'{df["Sido"]} {df["Sigun"]} {df["Dong"]}'
        else:
            address = f'{df["Sigun"]} {df["Dong"]}'
    return address
```

위의 부분 전처리 함수는 아래의 데이터셋을 생성하는 함수내에서 참조하여 사용한다
```python
def make_dataset(filename: str):
    """
    geojson 파일을 업로드 하기 위해 전처리 후 데이터를 반환한다

    :param filename:
    :return:
    """

    gdf = gpd.read_file(filename)
    gdf['geometry'] = gdf['geometry'].apply(lambda x: shapely.geometry.mapping(x))

    gdf['adm_nm'] = gdf['adm_nm'].str.replace('·', ',')
    gdf['Sido'] = gdf['sidonm']
    gdf['Sigun'] = gdf.apply(split_sido_sggnm, axis=1)
    gdf['Gu'] = gdf.apply(split_sggnm_gu, axis=1)
    gdf['Dong'] = gdf['adm_nm'].apply(lambda x: x.split()[-1])
    gdf['Address'] = gdf.apply(make_full_address, axis=1)
    gdf.drop(['adm_nm', 'sidonm', 'sggnm', 'sgg', 'sido'], axis=1, inplace=True)

    data = gdf.to_dict('records')

    return data
```

만들어진 데이터셋을 MongoDB에 insert하고 인덱스를 생성해준다
```python
import pymongo

from repositories.connectors import MongoDBConnector
from utils.address import make_dataset

if __name__ == '__main__':
    # 행정동 데이터를 저장하기 위해 MongoDB Connector 를 생성한다
    mdb_conn = MongoDBConnector().conn()
    collection = mdb_conn['Locations']['HangJeongDong']

    filename = "HangJeongDong_ver20210701.geojson"
    data = make_dataset(filename)
    collection.insert_many(data)

    # Create Index : geolocation
    # Geolocastion 인덱스를 생성한다
    collection.create_index([("geolocation", pymongo.GEOSPHERE)])

    # Create Index : Address
    # 각 시도, 시군, 구, 동, 주소별로 인덱스를 생성한다
    collection.create_index([("Sido", pymongo.DESCENDING)])
    collection.create_index([("Sigun", pymongo.DESCENDING)])
    collection.create_index([("Gu", pymongo.DESCENDING)])
    collection.create_index([("Dong", pymongo.DESCENDING)])
    collection.create_index([("Address", pymongo.DESCENDING)])
```

## Use Geolocation
MongoDB에 저장한 행정동 경계를 사용하는 방법은 $geoIntersector을 사용해서 위치와 교차하는 값을 찾는다

MongoDB Reference: [$geoIntersectors](https://docs.mongodb.com/manual/reference/operator/query/geoIntersects/)
```python
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
```

## Example
위 함수를 통해 다음과 같이 사용할 수 있다
```python
mdb_conn = MongoDBConnector().conn()
conn = mdb_conn["Locations"]["HangJeongDong"]
exam_lon = 127.0016985
exam_lat = 37.5642135

results = find_location_to_geopoint(client=conn, lat=exam_lat, lon=exam_lon)
print(results)
### Output
# {'Sido': '서울특별시', 'Sigun': '서울특별시', 'Gu': '중구', 'Dong': '광희동', 'Address': '서울특별시 중구 광희동'}
```

## 출처
 - **행정동 경계 파일 : [https://github.com/vuski/admdongkor](https://github.com/vuski/admdongkor)**
