import logging

from rich import print
from rich.logging import RichHandler
from rich.prompt import Confirm, IntPrompt

from . import buff, calc, steam

logger = logging.getLogger('main')


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)-8s %(message)s",
        handlers=[RichHandler(show_time=False, show_path=False)],
    )

    logger.debug("start")

    while True:
        try:
            min_price = IntPrompt.ask("Lowest price")
            max_price = IntPrompt.ask("Highest price")
            assert 0 <= min_price <= max_price <= 10000
        except KeyboardInterrupt:
            raise
        except:
            pass
        else:
            break

    if Confirm.ask("Update item from Buff ?", default=True):
        buff.solve(min_price, max_price)

    if Confirm.ask("Update item from Steam ?", default=True):
        steam.solve(min_price, max_price)

    print(calc.solve(min_price, max_price))

    logger.debug("end")
