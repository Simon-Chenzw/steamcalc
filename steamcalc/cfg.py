from typing import Any, List, Optional

import yaml
from pydantic import BaseModel

agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'


class SqliteConfig(BaseModel):
    name: str
    init_script: str


class ProxyConfig(BaseModel):
    url: str
    enable_clash: bool


class GoodsConfig(BaseModel):
    game: str
    category: List[str]
    category_group: List[str]

    def __init__(
        self,
        category: Optional[List[Optional[str]]],
        category_group: Optional[List[Optional[str]]],
        **data: Any,
    ) -> None:
        def fix(lst: Optional[List[Optional[str]]]) -> List[str]:
            if lst is None:
                return []
            return [obj for obj in lst if obj is not None]

        super().__init__(
            category=fix(category),
            category_group=fix(category_group),
            **data,
        )


class BuffConfig(BaseModel):
    cookie: str
    goods: List[GoodsConfig]


class DisplayConfig(BaseModel):
    max_row: int


class Config(BaseModel):
    expired_limit: int  # minute
    sqlite: SqliteConfig
    proxy: ProxyConfig
    buff: BuffConfig
    display: DisplayConfig


with open("cfg.yml", 'r') as fp:
    cfg = Config.parse_obj(yaml.load(fp, yaml.FullLoader))
