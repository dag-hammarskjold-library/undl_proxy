from io import BytesIO
from lxml import etree
from urllib import request
from urllib.error import HTTPError, URLError
from socket import timeout as sock_timeout


class TimeoutError(Exception):
    pass


class BasePage:
    """
        class variable DEFAULT_TIMEOUT
    """
    DEFAULT_TIMEOUT = 120  # 120 seconds

    def __init__(self):
        """
            set html parser from etree
        """
        self.parser = etree.HTMLParser()

    def get_root(self, url):
        html = self._get_html(url)
        root = etree.parse(BytesIO(html), self.parser)
        return root

    def _get_html(self, url, timeout=DEFAULT_TIMEOUT):
        """
            send request to @url
        """
        try:
            req = request.Request(url)
            response = request.urlopen(req, timeout=timeout)
            html = response.read()
        except (HTTPError, URLError) as err:
            print("Caught Error fetching from {0}, {1}".format(url, err))
            # it is bad policy to reraise errors
            # this is for demo only, IRL log error, move on to next url or stop
            raise(err)
        except sock_timeout:
            raise(TimeoutError("TimeoutException : {0}".format(url)))
        else:
            return html
