from typing import Callable, Dict, Any, List

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.engine import Engine

from doge import Subject, Transition
from doge import EventSink


class DbSink(EventSink):

    def __init__(self, engine: Engine, metadata: MetaData, table_name: str, row_mapper_function: Callable[[int, Subject, Transition], Dict[str, Any]], batch_size: int):
        self.engine = engine
        self.table = Table(table_name, metadata)
        self.batch = []
        self.row_mapper_function = row_mapper_function
        self.batch_size = batch_size

    def collect(self, timestamp: int, subject: Subject, transition: 'Transition'):
        row = self.row_mapper_function(timestamp, subject, transition)
        self.batch.append(row)
        if len(self.batch) >= self.batch_size:
            self.__insert_batch()

    def close(self):
        if len(self.batch):
            self.__insert_batch()

    def __insert_batch(self):
        self.engine.execute(self.table.insert(), self.batch)
        self.batch = []


class DbSinkFactory(object):
    batches: Dict[str, List[Dict[str, Any]]]
    tables: Dict[str, Table]

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        self.metadata.reflect(self.engine)
        self.batches = {}
        self.tables = {}

    def create(self, table_name: str, row_mapper_function: Callable[[int, Subject, Transition], Dict[str, Any]], batch_size: int = 1000):
        return DbSink(self.engine, self.metadata, table_name, row_mapper_function, batch_size)
