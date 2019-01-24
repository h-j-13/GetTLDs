#!/usr/bin/python
# encoding:utf-8

#
# WhoisSrv获取-来自INNA
# func  : 插入，更新信息
# time  : 2016.9.13
# author: @`13
#

import time
import datetime
import ConfigParser
import MySQLdb
from db_opreation import DataBase
from IANA_spider import spider

global DB_Str, TableStr
DB_Str = "whois_support"
TableStr = "whois_tld_addr"


class GetTLD:
    """TLD内容更新类"""

    def __init__(self):
        """实例化对象"""
        global DB_Str, TableStr
        self.db = DataBase()  # 实例数据库对象
        self.INNAspider = spider()  # 实例化一个爬虫对象
        self.staic = ConfigParser.ConfigParser()  # 实例化配置文件
        self.staic.read('GetTLDs.conf')
        self.Intervals = self.staic.getfloat('Spider', 'getIntervals')  # 获取间隔
        self.delta = self.staic.getint('Spider', 'delta')  # 更新间隔
        self.IANA_url = 'http://www.iana.org/domains/root/db'  # TLD数据地址
        self.db.get_connect()  # 连接到数据库

    def getCurrentTime(self):
        """:return 当前时间(datetime)"""
        return datetime.datetime.now()

    def isexist(self, tld):
        """判断这个TLD是否存在
        :return False-不存在 or insertTime：上次更新时间-存在"""
        SQL = """SELECT * FROM {db}.{table} WHERE TLD = '{tld}'""".format(
            tld=tld, db=DB_Str, table=TableStr)  # SQL语句

        result = self.db.execute(SQL)
        if result is None:
            return False
        elif result[0][4] == '':
            return 'No-whois'
        else:
            return self.db.execute(SQL)[0][6]

    def SQL_Generate(self, GenType='INSERT', **TLDinfo):
        """SQL语句生成
        :return 生成插入TLD信息的SQL代码"""
        TLD = TLDinfo['TLD']
        punycode = TLDinfo['punycode']
        Type = TLDinfo['type']
        WhoisSrv = TLDinfo['WhoisSrv']
        SponsoringOrganisation = TLDinfo['SponsoringOrganisation']
        # 生成SQL语句
        if GenType == 'INSERT':
            SQL = """INSERT {db}.{table} """.format(db=DB_Str, table=TableStr)
            SQL += """(`TLD`,`Punycode`,`Type`,`whois_addr`,`SponsoringOrganization`)"""
            SQL += """VALUES('{T}','{PC}','{Ty}','{WS}','{SO}');""". \
                format(T=TLD, PC=punycode, Ty=Type, WS=WhoisSrv, SO=SponsoringOrganisation)
        elif GenType == 'UPDATE':
            SQL = """UPDATE  {db}.{table} """.format(db=DB_Str, table=TableStr)
            SQL += """SET `whois_addr`='{WS}' """.format(WS=WhoisSrv)
            SQL += """WHERE `TLD` = '{T}';""".format(T=TLD)
        else:
            print "[Error_SQL]未预计到的生成SQL语句模式"
            return None
        return SQL

    def insertInfo(self, getIntervals=3):
        """插入信息
        :param @getIntervals 获取间隔"""
        # 获取基础页面信息
        print "[ HTTP ]获取页面信息中...",
        try:
            HtmlData = self.INNAspider.getPageText(self.IANA_url)
        except Exception as err:
            print "失败！"
            print "[Error_HTTP] 获取内容出现问题" + str(err)
            self.db.db_close()
        print "成功"
        # 处理信息
        for TLDinfo in self.INNAspider.getTLDinfo(HtmlData, intervalsTime=self.Intervals):
            Curtime = self.getCurrentTime()
            existFlag = self.isexist(TLDinfo['TLD'])
            delta = datetime.timedelta(days=15)  # 更新期限
            # 判断应该进行的操作
            if not existFlag:
                TLDinfo = spider.getTLDWhoisSrv(**TLDinfo)
                SQL = self.SQL_Generate(**TLDinfo)
                print "[INSERT]获取了" + str(TLDinfo['TLD']) + "的相关信息"
            elif existFlag == 'No-whois' or delta < Curtime - existFlag:
                TLDinfo = spider.getTLDWhoisSrv(**TLDinfo)
                SQL = self.SQL_Generate(GenType='UPDATE', **TLDinfo)
                print "[UPDATE]更新了" + str(TLDinfo['TLD']) + "的相关信息"
            else:
                SQL = None
                print "[ SKIP ]跳过了" + str(TLDinfo['TLD']) + "的相关信息"
            # 数据库更新
            if SQL is not None:
                try:
                    self.db.execute(SQL)
                    self.db.db_commit()
                except MySQLdb.Error as err:
                    print "[Error_DB] 数据库操作出现问题"
                    print str(err)
                    self.db.db_close()
            self.db.db_commit()  # 一轮循环提交一次事物


if __name__ == '__main__':
    GT = GetTLD()
    print GT.isexist('.com')
    # GT.insertInfo()
