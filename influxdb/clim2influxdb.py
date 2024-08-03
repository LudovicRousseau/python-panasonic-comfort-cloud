#!/usr/bin/env python3

"""Get air conditioning data from Panasonic cloud

Display the data for the current date and time

Exemple:
  Clim consigne=28.000000,inside=23
"""

import pcomfortcloud
import os
import argparse
import sys
import logging
import logging.handlers
import pprint
import datetime

LOGIN = os.environ['CONFORT_CLOUD_LOGIN']
PASSWORD = os.environ['CONFORT_CLOUD_PASSWORD']

logger = logging.getLogger(os.path.splitext(os.path.basename(sys.argv[0]))[0])
pp = pprint.PrettyPrinter(indent=2)


class CustomFormatter(argparse.RawDescriptionHelpFormatter,
                      argparse.ArgumentDefaultsHelpFormatter):
    pass


def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description=sys.modules[__name__].__doc__,
        formatter_class=CustomFormatter)

    g = parser.add_argument_group("clim2influxdb settings")
    g.add_argument("--current", action="store_true",
            default=False,
            help="return current values")
    g.add_argument("--day", metavar="N",
            type=str,
            help="date of the day to use. Ex 2019/08/08")
    g.add_argument("--month", metavar="N",
            type=str,
            help="date of the month to use. Ex 2019/08/08")

    g = parser.add_mutually_exclusive_group()
    g.add_argument("--debug", "-d", action="store_true",
        default=False,
        help="enable debugging")
    g.add_argument("--silent", "-s", action="store_true",
        default=False,
        help="don't log to console")

    return parser.parse_args(args)


def setup_logging(options):
    """Configure logging."""
    root = logging.getLogger("")
    root.setLevel(logging.WARNING)
    logger.setLevel(options.debug and logging.DEBUG or logging.INFO)
    if not options.silent:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(
            "%(levelname)s[%(name)s] %(message)s"))
        root.addHandler(ch)


def date2int(year, month, day, hour):
    dd = datetime.datetime(year, month, day, hour, 0, 0)
    return dd.strftime("%s000000000")


def get_device(login, password):
    session = pcomfortcloud.Session(login, password)
    session.login()

    devices = session.get_devices()
    logger.debug(pp.pformat(devices))

    device_id = devices[0]['id']
    logger.debug("Using device: " + device_id)

    return (session, device_id)


def get_historic(date, mode, db_name):
    dt = datetime.date.fromisoformat(date)
    year = dt.year
    month = dt.month
    day = dt.day
    date = "{:04}{:02}{:02}".format(year, month, day)
    logger.debug("Using date: " + date)

    (session, device_id) = get_device(LOGIN, PASSWORD)
    values = session.history(device_id, mode, date)
    # logger.debug(pp.pformat(values))

    historyDataList = values['parameters']['historyDataList']
    logger.debug(pp.pformat(historyDataList))

    hour = 0
    for record in historyDataList:
        if mode == 'Day':
            # 'dataTime': '20240803 00',
            hour = int(record['dataTime'].split(" ")[1])
        else:
            # 'dataTime': '20240825'
            dt = datetime.date.fromisoformat(record['dataTime'])
            day = dt.day

        temperatureInside = record['averageInsideTemp']

        # no or invalid data?
        if temperatureInside == -255:
            continue

        temperatureOutside = record['averageOutsideTemp']
        consigne = record['averageSettingTemp']
        consumption = record['consumption']
        res = "%s consigne=%f,inside=%f,consumption=%f" % (db_name, consigne,
                temperatureInside, consumption)
        if temperatureOutside != -255:
            res += ",outside=%f" % temperatureOutside
        res += " " + date2int(year, month, day, hour)
        print(res)


if __name__ == "__main__":
    options = parse_args()
    setup_logging(options)

    if options.current:
        logging.debug("Getting current values.")
        (session, device_id) = get_device(LOGIN, PASSWORD)
        values = session.get_device(device_id)
        logger.debug(pp.pformat(values))

        parameters = values['parameters']

        consigne = parameters['temperature']
        temperatureInside = parameters['temperatureInside']
        temperatureOutside = parameters['temperatureOutside']

        res = "Clim consigne=%f,inside=%d" % (consigne, temperatureInside)
        if parameters['power'] is pcomfortcloud.constants.Power.On:
            res += ",outside=%d,power=1" % temperatureOutside
        print(res)

    if options.day:
        logging.debug("Getting for day:", options.day)
        get_historic(options.day, 'Day', 'Clim_history')

    if options.month:
        logging.debug("Getting for month:", options.month)
        get_historic(options.month, 'Month', 'Clim_history_jour')
