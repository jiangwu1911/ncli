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
                                            url=conf.netis_url,
                                            token=conf.netis_token,
                                            viewname=s['viewname'],
                                            capname=s['capname'],
                                            riskcode=s['riskcode'])


def run_stats(options):
    # 连接数据库
    engine = create_engine('mysql://%s:%s@%s:3306/%s' %
                           (conf.db_config['user'],
                            conf.db_config['passwd'],
                            conf.db_config['host'],
                            conf.db_config['db']))
    Session = sessionmaker(bind=engine)
    db = Session()

    for s in conf.stats:
        if (options.daily and s['reporttype']=='daily') or \
                (options.daily and s['reporttype']=='weekly') or \
                (options.daily and s['reporttype']=='monthly'):
            try:
                stat = new_statistics(s)
                stat.create() 
                stat.get_status()
                stat.get_results(db)
                stat.delete()
                log.debug('Stats \'%s\' finished.' % s['name'])
            except Exception, e:
                log.error(traceback.format_exc())

    db.close()


def main():
    from optparse import OptionParser

    # 处理命令行参数
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage, version=VERSION)
    parser.add_option("-d", "--daily", action="store_true",
                      dest="daily",
                      default=False,
                      help="Run daily statistics.")
    parser.add_option("-w", "--weekly", action="store_true",
                      dest="weekly",
                      default=False,
                      help="Run weekly statistics.")
    parser.add_option("-m", "--monthly", action="store_true",
                      dest="monthly",
                      default=False,
                      help="Run monthly statistics.")
    options, args = parser.parse_args()

    init_log()
    log.debug("Begin to run statistics.")

    run_stats(options)

    log.debug("Run statistics complete.")


if __name__ == "__main__":
    main()
