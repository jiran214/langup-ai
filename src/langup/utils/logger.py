#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys
from langup import config


def get_logging_logger(file_name):
    logger = logging.getLogger(file_name)
    logger.setLevel(level=logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

    if 'console' in config.log['handlers']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level=logging.DEBUG)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    if 'file' in config.log['handlers']:
        filename = os.path.join(os.path.dirname(config.log['file_path']), f'{file_name}.log')
        file_handler = logging.FileHandler(filename)
        # file_handler = handlers.TimedRotatingFileHandler(filename=f'{file_name}.log', when='D')
        file_handler.setLevel(level=logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger