#!/usr/bin/env python3

import logging
from logging.handlers import RotatingFileHandler

def get_log(name):
    log_name = '/tmp/' + name + '.log'
    log_handler = RotatingFileHandler(log_name, maxBytes=52428800, backupCount=2)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(process)d --- [%(threadName)s] %(funcName)s : %(message)s')
    log_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG)
    return logger
