# -*- coding: UTF-8 -*-

import httplib2
import json
import logging
import time
import re
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Sequence
from sqlalchemy.ext.declarative import declarative_base
from Statistics import Statistics

log = logging.getLogger("ncli")

Base = declarative_base()

class TransactionSucRate(Base):
    __tablename__ = 'Rsk_SysTransactionSucRate'
    riskId = Column(String(36), primary_key=True)
    riskCode = Column(String(32))
    riskDate = Column(DateTime)
    snt = Column(Numeric(12, 0))
    tnt = Column(Numeric(12, 0))
    createTime = Column(DateTime)
    checkFlag = Column(Integer)
    uploadTime = Column(DateTime)
    uploadFlag = Column(Integer)
    dataFlag = Column(Integer)
    dataRemark = Column(String(128))

    def __init__(self):
        self.snt = 0
        self.tnt = 0
        self.checkFlag = 0
        self.uploadFlag = 0
        self.dataFlag = 0
        self.dataRemark = ''

    def __repr__(self):
        return("<Rsk_SysTransactionSucRate('%s', '%s', '%s', %d, %d, '%s', %d, '%s', %d, %d, '%s')>"
             % (self.riskId,
                self.riskCode,
                self.riskDate,
                self.snt,
                self.tnt,
                self.createTime,
                self.checkFlag,
                self.uploadTime,
                self.uploadFlag,
                self.dataFlag,
                self.dataRemark))


class TransactionSucRateStatistics(Statistics):
    _sid = ''
    _result_url = ''
    _delete_url = ''
    begin_time = ''
    end_time = ''

    def __init__(self, reportname='', url='', viewname='', capname='',
                 riskcode='', reporttype='', token=''):
        self.reportname = reportname
        self.url = url
        self.token = token
        self.viewname = viewname
        self.capname = capname
        self.indicators = re.split(',\s*', 'duration, trans_count, rr_rate, succ_rate')
        self.riskcode = riskcode
        self.reporttype = reporttype


    def create(self):
        h =  httplib2.Http()
        # 缺省是日报
        now = time.time()
        self.end_time = now - (now % 86400) + time.timezone
        self.begin_time = self.end_time - 86400

        data = { "earliest": "2015-09-07 01:15:00",
                 "latest": "2015-09-07 20:00:00",
                 #"earliest": time.ctime(self.begin_time),
                 #"latest": time.ctime(self.end_time),
                 "view_name": self.viewname,
                 "cap_name": self.capname,
                 "indicators": self.indicators }

        resp, content = h.request(self.url + 'stats',
                                  'POST',
                                  json.dumps(data),
                                  headers={'Content-Type': 'application/json',
                                           'Authorization': 'token %s' % self.token,
                                           'Accept': 'application/vnd.crossflow.bpc+json;indent=4'})
        #log.debug(resp)
        #log.debug(content)
        result = json.loads(content)
        if not result.has_key('sid'):
            raise Exception('Response does not contain sid.')            
        else:
            self._sid = result['sid']


    def get_status(self):
        h =  httplib2.Http()
        resp, content = h.request(self.url + 'stats/' + self._sid,
                                  'GET',
                                  headers={'Authorization': 'token %s' % self.token,
                                           'Accept': 'application/vnd.crossflow.bpc+json;indent=4'})
        #log.debug(resp)
        #log.debug(content)
        result = json.loads(content)
        if not result.has_key('state'):
            raise Exception('Response does not contain state.')
        elif result['state'] != '209 DONE':
            raise Exception('Statistics not ready')
        else:
            for link in result['links']:
                if link['rel'] == 'delete':
                    self._delete_url = link['href']
                if link['rel'] == 'results':
                    self._result_url = link['href']


    def get_results(self, db):
        if self._result_url == '':
            return
        h =  httplib2.Http()
        resp, content = h.request(self._result_url + "?offset=0&limit=2",
                                  'GET',
                                  headers={'Authorization': 'token %s' % self.token,
                                           'Accept': 'application/vnd.crossflow.bpc+json;indent=4'})
        #log.debug(resp)
        #log.debug(content)
        result = json.loads(content)
        if not result.has_key('items'):
            raise Exception('Stats result does not contain items.')
        items = result['items']
        if len(items) < 1:
            raise Exception('Stats result does not contain items.')
        
        trans_count = items[0]['trans_count']
        succ_rate = items[0]['succ_rate']

        # 查看数据库中是否已有记录,如果有先删除旧数据
        riskDate = time.strftime('%Y-%m-%d', time.gmtime(self.begin_time))
        db.query(TransactionSucRate).filter(TransactionSucRate.riskDate==riskDate,
                                            TransactionSucRate.riskCode==self.riskcode).delete()
        record = TransactionSucRate()
        record.riskId = self.get_risk_id()
        record.riskCode = self.riskcode
        record.riskDate = time.strftime('%Y-%m-%d', time.gmtime(self.begin_time))
        record.snt = trans_count * succ_rate / 100
        record.tnt = trans_count
        record.createTime = record.uploadTime = self.get_current_time()
        db.add(record)
        db.commit()
         

    def delete(self):
        if self._result_url == '':
            return
        h =  httplib2.Http()
        resp, content = h.request(self._delete_url,
                                  'DELETE',
                                  headers={'Authorization': 'token %s' % self.token,
                                           'Accept': 'application/vnd.crossflow.bpc+json;indent=4'})
        #log.debug(resp)
        #log.debug(content)
