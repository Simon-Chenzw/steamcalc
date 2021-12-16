import sqlite3
from contextlib import contextmanager
from decimal import Decimal

from .cfg import cfg

sqlite3.register_adapter(
    Decimal,
    lambda dec: str(dec),
)
sqlite3.register_converter(
    "DECIMAL",
    lambda byte: Decimal(byte.decode('ascii')),
)


class DataBase:
    def __init__(self, name: str, init_script: str) -> None:
        self.con = sqlite3.connect(name, detect_types=sqlite3.PARSE_DECLTYPES)
        with self.cursor() as cur:
            cur.executescript(init_script)

    @contextmanager
    def cursor(self):
        cur = self.con.cursor()
        try:
            yield cur
        finally:
            self.con.commit()

    def __del__(self):
        self.con.close()

    def clean(self):
        # TODO clean expired record
        pass  


with open(cfg.sqlite.init_script, 'r') as fp:
    db = DataBase(cfg.sqlite.name, fp.read())
