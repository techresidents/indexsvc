#!/usr/bin/env python

"""index_job_scheduler.py
This script is designed to make it easy to manually create an IndexJob.
It is designed to be run locally.  It will populate the IndexJob table
with the data specified as arguments.  If you need to create an IndexJob on
production, simply dump your local IndexJob table.
options:
    -i --index=INDEX     index name (Required)
    -t --type=TYPE       document type (Required)
    -k --keys=KEY        comma separated string of document keys (Optional. Defaults to all keys)
    -d --days=DAYS       number of days to schedule an IndexJob (Optional. Defaults to 1. Max of 90. First job is scheduled for today)
    -T --time=HH:MM      time string that specifies when the job will be run (Optional. Defaults to midnight)
    -c --context=CONTEXT index job context (Optional. Defaults to 'index_job_scheduler')
    -p --preview         Flag to preview your configuration options (Optional. Defaults to False)
"""
import datetime
import getopt
import os
import sys
import time

from trindexsvc.gen import TIndexService
from trindexsvc.gen.ttypes import IndexData
from trpycore.timezone import tz
from trpycore.zookeeper.client import ZookeeperClient
from trsvcscore.proxy.zoo import ZookeeperServiceProxy

PROJECT_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SERVICE =  os.path.basename(PROJECT_DIRECTORY)
SERVICE_DIRECTORY = os.path.join(PROJECT_DIRECTORY, SERVICE)
sys.path.insert(0, SERVICE_DIRECTORY)

import settings


class Usage(Exception):
    def __str__(self):
        return __doc__

class Config(object):

    def __init__(self, argv):
        self.MAX_DAYS = 90
        self.preview = False
        self.indexjob_context = "index_job_scheduler"
        self.days = 1
        self.time = tz.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        self.index_name = None
        self.doc_type = None
        self.keys = []
        try:
            options, arguments = getopt.getopt(argv, "hpc:i:t:k:d:T:",["help", "preview", "context=", "index=", "type=", "keys=", "days=", "time="])

            for option, argument in options:
                if option in ("-h", "--help"):
                    raise Usage()
                elif option in ("-p", "--preview"):
                    self.preview = True
                elif option in ("-c", "--context"):
                    self.indexjob_context = argument
                elif option in ("-i", "--index"):
                    self.index_name = argument
                elif option in ("-t", "--type"):
                    self.doc_type = argument
                elif option in ("-k", "--keys"):
                    k = argument.replace(" ", "")
                    self.keys = k.split(',')
                elif option in ("-d", "--days"):
                    self.days = int(argument)
                elif option in ("-T", "--time"):
                    t = argument.split(':')
                    hour = int(t[0])
                    minute = int(t[1])
                    self.time = self.time.replace(hour=hour, minute=minute)
                else:
                    raise Usage()

            if (not self.index_name or
                not self.doc_type or
                self.days > self.MAX_DAYS):
                raise Usage()

        except Exception as e:
            raise Usage()

def main(argv):

    def get_index_data(config):
        not_before = tz.utc_to_timestamp(config.time)
        return IndexData(
            notBefore=not_before,
            name=config.index_name,
            type=config.doc_type,
            keys=config.keys
        )

    def get_zookeeper_client():
        zookeeper_client = ZookeeperClient(settings.ZOOKEEPER_HOSTS)
        zookeeper_client.start()
        time.sleep(1)
        return zookeeper_client

    def get_index_svc_proxy(zookeeper_client):
        return ZookeeperServiceProxy(
            zookeeper_client,
            service_name="indexsvc",
            service_class=TIndexService,
            keepalive=True
        )

    try:
        zookeeper_client = None
        config = Config(argv)
        print '################################################'
        print "Using these configuration options:"
        print "Index name: %s" % config.index_name
        print "Document type: %s" % config.doc_type
        print "Db keys: %s" % config.keys
        print "Number of days: %s" % config.days
        print "IndexJob start time (HH:MM): %s:%s" % (config.time.hour, config.time.minute)
        print "IndexJob context: %s" % config.indexjob_context
        print '################################################'

        if not config.preview:
            # Get hook into index service
            zookeeper_client = get_zookeeper_client()
            index_svc_proxy = get_index_svc_proxy(zookeeper_client)

            # Create a job for each day
            for day in range(config.days):
                # after first iteration, add one day to start time
                # range() is zero-based
                if day:
                    config.time = config.time + datetime.timedelta(days=1)
                index_data = get_index_data(config)

                # invoke index() or indexAll() depending if we have a list of keys
                if len(config.keys):
                    index_svc_proxy.index(config.indexjob_context, index_data)
                else:
                    index_svc_proxy.indexAll(config.indexjob_context, index_data)

        # Boom. Done.
        return 0

    except Usage, error:
        print str(error)
    except Exception, error:
        print '**************************************************'
        print 'Exception'
        print '%s' % str(error)
        print '**************************************************'
    finally:
        if zookeeper_client:
            zookeeper_client.stop()
            zookeeper_client.join()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))