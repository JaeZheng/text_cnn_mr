# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os
import datetime


class Logger:
    def __init__(self, log_file=None):
        # 创建日志文件
        self.make_path(log_file)

        # 实例化handler
        self.handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8')
        self.fmt = '%(asctime)s - %(levelname)s - %(message)s'

        self.formatter = logging.Formatter(self.fmt)  # 实例化formatter
        self.handler.setFormatter(self.formatter)  # 为handler添加formatter

        self. logger = logging.getLogger()  # logger
        self.logger.addHandler(self.handler)  # 为logger添加handler
        self.logger.setLevel(logging.DEBUG)

    def info(self, message):
        self.logger.info(message)
        self.log_info(message)

    def debug(self, message):
        self.logger.debug(message)
        self.log_info(message)

    def make_path(self, file_path):
        file_dir = os.path.split(file_path)[0]
        if not os.path.exists(file_dir):  # 判断文件夹是否存在
            os.mkdir(file_dir)  # 如果不存在, 创建文件夹
        if not os.path.exists(file_path):  # 判断文件是否存在
            os.system(r'touch %s' % file_path)

    def log_info(self, message):
        time = str(datetime.datetime.now())
        print("[%s]" % time + message)


