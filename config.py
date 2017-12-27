import re


class Config(object):
    DEBUG = False
    TESTING = False
    BASE_URL = 'http://dag.un.org'
    PATH = '/docs'

    SUBJECT_RE = re.compile(r"""
        ^\d{6,7}\s(?:unbis[nt])*\s*(.+)$|
        ^([a-zA-Z ]+)\sunbis[nt]\s\d+$|
        ^unbist\s([a-zA-Z ]+)\s\(DHLAUTH\)\d+$|
        ([a-zA-Z ]+)\sunbist\s\(DHLAUTH\)\d+$""", re.X)

    RELDOC_RE = re.compile(r'^([a-zA-Z0-9\/]+)(\(\d{4}\))$')

    DB_URI = 'sqlite:////tmp/undl_url.db'


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
