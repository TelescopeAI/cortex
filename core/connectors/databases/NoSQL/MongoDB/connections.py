from typing import Any, Optional

from core.types.ts_model import TSModel
from pymongo import MongoClient


class MongoDB(TSModel):
    client: Optional[Any] = None

    def new_client(self, host: str = "localhost", port: int = 27017):
        self.client = MongoClient(host, port)
        return self.client

    def get_database(self, db_name: str):
        if self.client is not None:
            return self.client[db_name]
        else:
            raise Exception('No client found')

    def get_collection(self, db_name: str, collection_name: str):
        if self.client is not None:
            return self.client[db_name][collection_name]
        else:
            raise Exception('No client found')

    def insert_one(self, db_name: str, collection_name: str, data: dict):
        if self.client is not None:
            return self.client[db_name][collection_name].insert_one(data)
        else:
            raise Exception('No client found')


