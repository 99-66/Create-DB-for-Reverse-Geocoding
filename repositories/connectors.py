from pymongo import MongoClient
from repositories.env import MONGODB


class MongoDBConnector:
    mongodb = MONGODB

    def __init__(self, client=None):
        if client:
            self.client = client
        else:
            self.client = MongoClient(self._default())

        self.db = self._database()

    @classmethod
    def _default(cls) -> str:
        conn = f'mongodb://{cls.mongodb["USER"]}:{cls.mongodb["PASSWORD"]}@{cls.mongodb["HOST"]}:{cls.mongodb["PORT"]}/'
        if cls.mongodb['SSL'] and cls.mongodb['SSL'] is True:
            conn = f'{conn}?ssl=true'
            if cls.mongodb['SSL_CA_CERTS']:
                conn = f'{conn}&ssl_ca_certs={cls.mongodb["SSL_CA_CERTS"]}'
        else:
            conn = f'{conn}?ssl=false'

        if cls.mongodb['REPLICA_SET']:
            conn = f'{conn}&replicaSet={cls.mongodb["REPLICA_SET"]}'

        return conn

    @classmethod
    def _database(cls) -> str:
        return cls.mongodb['DB']

    def conn(self) -> MongoClient:
        return self.client

    def upsert(self, db: str, table: str, data: dict) -> bool:
        """
        전달받은 Table 에 Data 를 업데이트(Upsert) 한다

        :param db:
        :param table:
        :param data:
        :return:
        """

        if '_id' not in data:
            raise TypeError('_id field is missing')
        try:
            self.client[db][table].replace_one({'_id': data['_id']}, data, upsert=True)
        except Exception as e:
            raise Exception(repr(e))
        else:
            return True
