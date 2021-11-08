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
