import re


class Config(object):
    DEBUG = False
    TESTING = False
    SUBJECT_RE = re.compile(r"""
        ^\d{6,7}\s(?:unbis[nt])*\s*(.+)$|
        ^([a-zA-Z ]+)\sunbis[nt]\s\d+$|
        ^unbist\s([a-zA-Z ]+)\s\(DHLAUTH\)\d+$|
        ([a-zA-Z ]+)\sunbist\s\(DHLAUTH\)\d+$""", re.X)
    RELDOC_RE = re.compile(r'^([a-zA-Z0-9\/]+)(\(\d{4}\))$')


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
