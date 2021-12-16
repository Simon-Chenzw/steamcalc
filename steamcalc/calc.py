import sqlite3
import time
from decimal import Decimal
from functools import cached_property
from typing import List

from pydantic import BaseModel, parse_obj_as
from rich.table import Column, Table

from .cfg import cfg
from .db import db


class Result(BaseModel):
    name: str

    # steam related
    sell: Decimal
    buy: Decimal

    # buff related
    third_sell: Decimal
    third_buy: Decimal
    url: str

    class Config:
        keep_untouched = (cached_property, )

    @cached_property
    def immediately_get(self) -> Decimal:
        tax_rate = Decimal(0.15)
        return self.buy / (Decimal(1) + tax_rate)

    @cached_property
    def discount(self) -> Decimal:
        return self.third_sell / self.immediately_get


class Results:
    def __init__(self, lst: List[Result]) -> None:
        self.lst = lst

    def __rich__(self):
        table = Table(
            Column("名称"),
            Column("买入价"),
            Column("卖出价"),
            Column("收入"),
            Column("折扣"),
            title="Steam Calculator",
        )

        def display(dec: Decimal) -> str:
            return str(dec.quantize(Decimal('0.01')))

        for res in sorted(
                self.lst,
                key=lambda res: res.discount,
        )[:cfg.display.max_row]:
            table.add_row(
                f"[link={res.url}]{res.name}[/link]",
                display(res.third_sell),
                display(res.buy),
                display(res.immediately_get),
                display(res.discount),
            )

        return table

    @classmethod
    def getFromDB(cls, min_price: int, max_price: int):
        time_lim = int(time.time()) - cfg.expired_limit * 60
        with db.cursor() as cur:
            cur.row_factory = sqlite3.Row
            ret: List[sqlite3.Row] = cur.execute(
                """
                select
                    locale.name         as  name,
                    market.lowest_sell  as  sell,
                    market.highest_buy  as  buy,
                    buff.lowest_sell    as  third_sell,
                    buff.highest_buy    as  third_buy,
                    buff.url            as  url
                from 
                    market
                inner join buff on
                    market.item_id = buff.item_id
                inner join locale on 
                    market.item_id = locale.item_id
                where
                        buff.lowest_sell >= ?
                    and buff.highest_buy <= ?
                    and buff.update_time >= ?
                    and market.update_time >= ?;
                """,
                (
                    min_price,
                    max_price,
                    time_lim,
                    time_lim,
                ),
            ).fetchall()

        return cls(parse_obj_as(List[Result], ret))


solve = Results.getFromDB
