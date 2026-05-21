import logging


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="time=%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
    )
