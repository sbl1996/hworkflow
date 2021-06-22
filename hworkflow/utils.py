import os
import base64
from datetime import datetime

from dateutil.parser import parse
import pytz


def format_url(url):
    if not url.startswith("http") and not url.startswith("https"):
        url = "http://" + url
    if url.endswith("/"):
        url = url[:-1]
    return url


def parse_datetime(dt):
    dt = parse(dt)
    dt = dt.replace(tzinfo=None, microsecond=0)
    return dt


def format_datetime(dt: datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def datetime_now(format=False):
    dt = datetime.now(tz=pytz.timezone("Asia/Shanghai"))
    dt = dt.replace(tzinfo=None, microsecond=0)
    if format:
        dt = format_datetime(dt)
    return dt


def set_proxy(port):
    os.environ['HTTP_PROXY'] = os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:%d' % port


def unset_proxy():
    del os.environ['HTTP_PROXY']
    del os.environ['HTTPS_PROXY']


def encode_script(script: str):
    return base64.b64encode(script.encode()).decode()

def decode_script(encoded_scirpt):
    return base64.b64decode(encoded_scirpt.encode()).decode()