import socket

from default_settings import *

ENV = "prod"

#Service Settings
SERVICE = "indexsvc"
SERVICE_PID_FILE = "/opt/tr/data/%s/pid/%s.%s.pid" % (SERVICE, SERVICE, ENV)
SERVICE_JOIN_TIMEOUT = 1

#Server settings
THRIFT_SERVER_ADDRESS = socket.gethostname()
THRIFT_SERVER_INTERFACE = "0.0.0.0"
THRIFT_SERVER_PORT = 9096

#Database settings
DATABASE_HOST = "localhost"
DATABASE_NAME = "techresidents"
DATABASE_USERNAME = "techresidents"
DATABASE_PASSWORD = "t3chResident$"
DATABASE_CONNECTION = "postgresql+psycopg2://%s:%s@/%s?host=%s" % (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_HOST)

#Zookeeper settings
ZOOKEEPER_HOSTS = ["localhost:2181"]

#Index svc settings
INDEXER_THREADS = 1
INDEXER_POOL_SIZE = 1
INDEXER_POLL_SECONDS = 300
INDEXER_JOB_RETRY_SECONDS = 300
INDEXER_JOB_MAX_RETRY_ATTEMPTS = 3

#ElasticSearch settings
ES_ENDPOINT = "http://localhost:9200"
ES_POOL_SIZE = 1

#Logging settings
LOGGING = {
    "version": 1,

    "formatters": {
        "brief_formatter": {
            "format": "%(levelname)s: %(message)s"
        },

        "long_formatter": {
            "format": "%(asctime)s %(levelname)s: %(name)s %(message)s"
        }
    },

    "handlers": {

        "console_handler": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "brief_formatter",
            "stream": "ext://sys.stdout"
        },

        "file_handler": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "long_formatter",
            "filename": "/opt/tr/data/%s/logs/%s.%s.log" % (SERVICE, SERVICE, ENV),
            "when": "midnight",
            "interval": 1,
            "backupCount": 7
        }
    },

    "root": {
        "level": "INFO",
        "handlers": ["console_handler", "file_handler"]
    }
}