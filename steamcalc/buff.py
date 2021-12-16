import logging
import time
from decimal import Decimal
from functools import cached_property
from typing import Any, Dict, Iterator, List, Optional

import requests
from pydantic import BaseModel, parse_obj_as

from . import steam
from .cfg import agent, cfg
from .db import db

logger = logging.getLogger('buff')


class Item(BaseModel):
    appid: int
    name: str
    market_hash_name: str
    id: int
    sell_min_price: Decimal
    buy_max_price: Decimal

    class Config:
        keep_untouched = (cached_property, )

    @cached_property
    def item_id(self) -> int:
        return steam.get_item_id(self.appid, self.market_hash_name)

    @cached_property
    def url(self) -> str:
        return f"https://buff.163.com/goods/{self.id}?from=market#tab=selling"

    def insert(self) -> None:
        """
        CREATE TABLE IF NOT EXISTS buff(
            item_id INTEGER PRIMARY KEY,
            url TEXT,
            lowest_sell DECTEXT,
            highest_buy DECTEXT,
            update_time INTEGER
        );
        """
        logger.info(f"insert: {self.name}")
        with db.cursor() as cur:
            cur.execute(
                """
                insert into buff 
                    (item_id, url, lowest_sell, highest_buy, update_time) 
                values 
                    (?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    lowest_sell=excluded.lowest_sell,
                    highest_buy=excluded.highest_buy,
                    update_time=excluded.update_time;
                """,
                (
                    self.item_id,
                    self.url,
                    self.sell_min_price,
                    self.buy_max_price,
                    int(time.time()),
                ),
            )
            cur.execute(
                "insert or ignore into locale (item_id, name) values (?, ?)",
                (self.item_id, self.name),
            )


# TODO 检查当前cate是否已经爬过
def solve(min_price: Optional[int] = None, max_price: Optional[int] = None):
    for c in cfg.buff.goods:
        for cate in c.category:
            for item in getGoods(
                    c.game,
                    cate,
                    None,
                    min_price,
                    max_price,
            ):
                item.insert()

        for categ in c.category_group:
            for item in getGoods(
                    c.game,
                    None,
                    categ,
                    min_price,
                    max_price,
            ):
                item.insert()


def getGoods(
    game: str = 'csgo',
    category: Optional[str] = None,
    category_group: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
) -> Iterator[Item]:
    assert not (category is not None and category_group
                is not None), "Cannot specify two categories at the same time"
    if category:
        logger.info(f"crawler: {category}")
    elif category_group:
        logger.info(f"crawler: {category_group}")
    else:
        logger.info(f"crawler: all")

    params: Dict[str, Any] = {
        'game': game,
        'use_suggestion': 0,
        'trigger': 'undefined_trigger',
    }
    if category: params['category'] = category
    if category_group: params['category_group'] = category_group
    if min_price: params['min_price'] = min_price
    if max_price: params['max_price'] = max_price

    session = requests.Session()
    session.headers.update({
        "User-Agent": agent,
        "Cookie": cfg.buff.cookie,
    })

    for page in range(1, 100):
        logger.debug(f"crawler page: {page=}")
        res = session.get(
            'https://buff.163.com/api/market/goods',
            params={
                **params,
                'page_num': page,
                '_': time.time_ns(),
            },
        )
        assert res.status_code == 200
        js = res.json()
        yield from parse_obj_as(List[Item], js['data']['items'])
        if page == js['data']['total_page']:
            break
