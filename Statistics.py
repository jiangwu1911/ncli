# -*- coding: UTF-8 -*-

import uuid
import time

class Statistics:
    def __init__():
        pass

    def create(self):
        pass

    def get_status(self):
        pass

    def get_results(self, db):
        pass

    def delete(self):
        pass

    def get_risk_id(self):
        return uuid.uuid1()        

    def get_current_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
