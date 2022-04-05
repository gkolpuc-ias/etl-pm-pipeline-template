import argparse
import logging
import os
from argparse import ArgumentParser
from datetime import datetime

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(format="%(levelname)s: %(message)s", level=LOG_LEVEL)
logger = logging.getLogger(__name__)

DATE_FORMAT = '%Y%m%d'


def valid_date(date_string):
    try:
        return datetime.strptime(date_string, DATE_FORMAT)
    except ValueError as val_err:
        msg = f"Date {date_string} must be in format {DATE_FORMAT}"
        raise argparse.ArgumentTypeError(msg) from val_err


def get_args():
    parser = ArgumentParser(description="PARTNER_NAME - SERVICE_NAME.")

    parser.add_argument('--date', help=' format YYYY-MM-DD', type=valid_date)

    args = parser.parse_args()
    return args


def main():
    _args = get_args()
    logger.info("Starting SERVICE_NAME with parameters: %s", _args.__dict__)

    # TODO
    # Implement your service


if __name__ == "__main__":
    main()
