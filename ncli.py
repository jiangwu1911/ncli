# -*- coding: UTF-8 -*-

import logging
import logging.config
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import traceback

from TransactionSucRate import TransactionSucRateStatistics
import settings as conf


VERSION ="0.1"
log = logging.getLogger("ncli")

def init_log():
    logging.config.fileConfig("logging.conf")
    logger = logging.getLogger("ncli")


def new_statistics(s):
    if s['reportname'] == 'TransactionSucRateStatistics':
        return TransactionSucRateStatistics(reportname=s['reportname'],
                                            reporttype=s['reporttype'],
                                            url=s['url'],
                                            token=conf.netis_token,
                                            viewname=s['viewname'],
                                            capname=s['capname'],
                                            riskcode=s['riskcode'])


def run_stats(db):
    for s in conf.stats:
        try:
            stat = new_statistics(s)
            stat.create() 
            stat.get_status()
            stat.get_results()
            stat.delete()

        except Exception, e:
            log.error(traceback.format_exc())


def main():
    from optparse import OptionParser

    usage = "Usage: %prog [options]"
    parser = OptionParser(usage, version=VERSION)
    options, args = parser.parse_args()

    init_log()
    log.debug("Begin to run statistics.")

    engine = create_engine('mysql://%s:%s@%s:3306/%s' % 
                           (conf.db_config['user'],
                            conf.db_config['passwd'],
                            conf.db_config['host'],
                            conf.db_config['db']))
    Session = sessionmaker(bind=engine)
    db = Session()

    run_stats(db)

    db.close()
    log.debug("Run statistics complete.")


if __name__ == "__main__":
    main()
