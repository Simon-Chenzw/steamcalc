import logging
from itertools import chain
from typing import Any, Dict, List, Literal, Optional, Union

import requests
from pydantic import BaseModel, parse_raw_as

from .cfg import ClashEnableConfig, cfg

logger = logging.getLogger('proxy')

if not cfg.proxy.clash.enable:

    def change_proxy() -> None:
        """
        暂停手动切换proxy
        """

        logger.warning("please change proxy manual")
        input()

else:
    assert isinstance(cfg.proxy.clash, ClashEnableConfig)
    clash_cfg: ClashEnableConfig = cfg.proxy.clash

    def change_proxy() -> None:
        """
        自动切换 clash 代理
        """

        p = proxy_get(clash_cfg.selector)
        assert isinstance(p, ClashSelectorProxy)

        lst = sorted(p.all)
        idx = lst.index(p.now)
        for name in chain(lst[idx + 1:], lst[:idx]):
            logger.debug(f"now testing {name=}")
            if proxy_check(name) and proxy_set(clash_cfg.selector, name):
                logger.info(f"change proxy of {clash_cfg.selector}: {name}")
                break


def proxy_check(name: str) -> bool:
    """
    检查 proxy 能否选择，且是否正常
    """
    p = proxy_get(name)
    if p.type not in ['Shadowsocks', 'Socks5', 'Vmess']:
        return False
    delay = proxy_delay(name, clash_cfg.test_timeout, clash_cfg.test_url)
    return delay is not None


def proxy_get_all() -> 'ClashProxies':
    logger.debug("get all proxies from clash")
    res = requests.get(f'http://{clash_cfg.api_url}/proxies')
    return ClashProxies.parse_raw(res.text)


def proxy_get(name: str) -> 'ClashProxy':
    logger.debug(f"get proxy {name=} from clash")
    res = requests.get(f'http://{clash_cfg.api_url}/proxies/{name}')
    return parse_raw_as(ClashProxy, res.text)


def proxy_delay(name: str, timeout: int, url: str) -> Optional[int]:
    """
    超时返回 None
    """
    logger.debug(f"test proxy {name=} delay to {url=} in {timeout=} ms")
    res = requests.get(
        f"http://{clash_cfg.api_url}/proxies/{name}/delay",
        params={
            'timeout': timeout,
            'url': url,
        },
    )
    obj: Dict[str, Any] = res.json()
    logger.debug(f"test proxy {name=} delay result: {obj}")
    return obj.get('delay', None)


def proxy_set(name: str, new_proxy: str) -> bool:
    logger.debug(f"set proxy {name=} to {new_proxy=}")
    res = requests.put(
        f"http://{clash_cfg.api_url}/proxies/{name}",
        json={'name': new_proxy},
    )

    logger.debug(
        f"set proxy {name=} return code: {res.status_code} {res.text}")

    return res.status_code == 204


class ClashDirectProxy(BaseModel):
    type: Literal['Direct']


class ClashRejectProxy(BaseModel):
    type: Literal['Reject']


class ClashSelectorProxy(BaseModel):
    type: Literal['Selector']
    name: str
    all: List[str]
    now: str


class ClashURLTestProxy(BaseModel):
    type: Literal['URLTest']


class ClashFallbackProxy(BaseModel):
    type: Literal['Fallback']


class ClashShadowsocksProxy(BaseModel):
    type: Literal['Shadowsocks']
    name: str


class ClashSocks5Proxy(BaseModel):
    type: Literal['Socks5']
    name: str


class ClashVmessProxy(BaseModel):
    type: Literal['Vmess']
    name: str


ClashProxy = Union[ClashDirectProxy, ClashRejectProxy, ClashSelectorProxy,
                   ClashURLTestProxy, ClashFallbackProxy,
                   ClashShadowsocksProxy, ClashSocks5Proxy, ClashVmessProxy, ]


class ClashProxies(BaseModel):
    proxies: Dict[str, ClashProxy]
