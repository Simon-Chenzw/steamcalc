import logging

logger = logging.getLogger('proxy')


def change_proxy() -> None:
    """
    暂停手动切换proxy
    """
    # TODO change clash proxy
    logger.warning("please change proxy manual")
    input()
