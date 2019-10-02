#!/usr/bin/env python3

"""Get air conditioning data from Panasonic cloud

Display the data for the current date and time
"""

import pcomfortcloud
import os
import argparse
import sys
import logging
import logging.handlers
import pprint

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
    g.add_argument("--date", action="store",
        type=str, help="date like 20190925")

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


def main(options):
    LOGIN = os.environ['CONFORT_CLOUD_LOGIN']
    PASSWORD = os.environ['CONFORT_CLOUD_PASSWORD']

    if options.date:
        logging.debug("Getting for date:", options.date)

    session = pcomfortcloud.Session(LOGIN, PASSWORD)
    session.login()

    devices = session.get_devices()
    logger.debug(pp.pformat(devices))

    device = devices[0]['id']
    logger.debug("Using device: " + device)

    if options.date:
        logger.debug("Getting date for date: " + options.date)
        values = session.history(device, "Day", options.date)
        logger.debug(pp.pformat(values))
        res = ""
    else:
        values = session.get_device(device)
        logger.debug(pp.pformat(values))

        parameters = values['parameters']

        consigne = parameters['temperature']
        temperatureInside = parameters['temperatureInside']
        temperatureOutside = parameters['temperatureOutside']

        res = "Clim consigne=%f,inside=%d" % (consigne, temperatureInside)
        if parameters['power'] is pcomfortcloud.constants.Power.On:
            res += ",outside=%d,power=1" % temperatureOutside

    return res


if __name__ == "__main__":
    options = parse_args()
    setup_logging(options)

    try:
        logger.debug("Get air conditionning data")
        res = main(options)
        print(res)
    except Exception as e:
        logger.exception("%s", e)
        sys.exit(1)
