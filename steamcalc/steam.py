import logging
import re
import time
from decimal import Decimal
from typing import Any, Dict, List, Tuple

import requests
from pydantic import BaseModel

from . import proxy
from .cfg import cfg
from .db import db

logger = logging.getLogger('steam')


class Item(BaseModel):
    item_nameid: int  # extra
    success: int
    highest_buy_order: int
    lowest_sell_order: int

    @classmethod
    def getFromID(cls, item_nameid: int):
        logger.debug(f"get: {item_nameid=}")
        res = requests.get(
            'https://steamcommunity.com/market/itemordershistogram',
            params={
                'country': 'CN',
                'language': 'schinese',
                'currency': 23,
                'item_nameid': item_nameid,
                'two_factor': 0,
            },
            proxies=cfg.proxy.url,
        )
        assert res.status_code == 200
        json: Dict[str, Any] = res.json()

        json['item_nameid'] = item_nameid
        obj = cls.parse_obj(json)
        assert obj.success == 1

        return obj

    def insert(self):
        with db.cursor() as cur:
            logger.info(f"insert: item_id={self.item_nameid}")
            cur.execute(
                """
                insert into market 
                    (item_id, lowest_sell, highest_buy, update_time) 
                values 
                    (?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    lowest_sell=excluded.lowest_sell,
                    highest_buy=excluded.highest_buy,
                    update_time=excluded.update_time;
                """,
                (
                    self.item_nameid,
                    Decimal(self.lowest_sell_order) / 100,
                    Decimal(self.highest_buy_order) / 100,
                    int(time.time()),
                ),
            )


def solve(min_price: int, max_price: int):
    with db.cursor() as cur:
        time_lim = int(time.time()) - cfg.expired_limit * 60
        need: List[Tuple[int]] = cur.execute(
            """
            select item_id from buff 
            where 
                    lowest_sell >= ? 
                and lowest_sell <= ? 
                and update_time >= ?
            EXCEPT
            select item_id from market 
            where update_time >= ?
            ;
            """,
            (
                min_price,
                max_price,
                time_lim,
                time_lim,
            ),
        ).fetchall()
        print(need)
    for item_id, in need:
        while True:
            try:
                item = Item.getFromID(item_id)
            except Exception as err:
                logger.warning(f"{err} at get item")
            else:
                logger.debug(f"got: {item_id=}")
                item.insert()
                break


def get_item_id(appid: int, hash_name: str) -> int:
    """
    在表中查找，没有就插入
    CREATE TABLE IF NOT EXISTS idmap(
        appid INTEGER,
        hash_name TEXT,
        item_id INTEGER,
        primary key (appid, hash_name)
    );
    """
    with db.cursor() as cur:
        obj = cur.execute(
            "select item_id from idmap where appid = ? and hash_name = ?;",
            (appid, hash_name),
        ).fetchone()
        if obj is not None:
            return obj[0]

    item_id = get_item_id_crawler(appid, hash_name)
    with db.cursor() as cur:
        cur.execute(
            "insert into idmap (appid, hash_name, item_id) values (?, ?, ?);",
            (appid, hash_name, item_id),
        )
    return item_id


def get_item_id_crawler(appid: int, hash_name: str) -> int:
    """
    爬取 steam 网页
    """
    def crawler() -> int:
        url = f"https://steamcommunity.com/market/listings/{appid}/{hash_name}"
        res = requests.get(url, proxies=cfg.proxy.url)
        assert res.status_code == 200

        match = re.search(
            r'Market_LoadOrderSpread\( (\d*) \);',
            res.text,
        )
        assert match
        item_id = int(match.group(1))
        return item_id

    while True:
        try:
            item_id = crawler()
        except Exception as err:
            logger.warning(f"'{err}' at get item_id")
            proxy.change_proxy()
        else:
            logger.info(f"get: {item_id=}")
            return item_id
