#!/usr/bin/python
# encoding:utf-8

#
# WhoisSrv获取-来自INNA
# func  : 主程序
# time  : old
# author: @`13
#

import time
import schedule

from insert_info import GetTLD

GT = GetTLD()
schedule.every(2).hours.do(GT.insertInfo)
while True:
    schedule.run_pending()
    time.sleep(1)
