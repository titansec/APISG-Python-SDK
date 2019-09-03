# coding=utf-8
import sys
import requests
from apig_sdk import signer

if sys.version_info.major < 3:
    from urllib import quote
else:
    from urllib.parse import quote

if __name__ == '__main__':
    sig = signer.Signer()
    sig.Key = "725e57fd-09fa-454b-bf37-ad41190b660c-c6adbafd-9420-49b1-9d91-905bd70ce6de"
    sig.Secret = "25EF9023B9AF78EDE2136C95EA44A764"

    r = signer.HttpRequest()
    r.scheme = "http"
    r.host = "192.168.36.144" 
    r.method = "GET"
   #uri 的特殊字符需用 quote 进行 urlencode 编码
    r.uri = "/a/v1/v2/v3/v4"
    r.query = {'qv9': 'v9', 'qv10': 'v10', 'qv11': 'v11', 'qv12': 'v12', 'miracle': 'qijian', 'str': '1 order by 1', 'json':'{"remote_addr":"1.1.1.1"}', 'where':'{"version":{"$gt":24811}}'}
    r.headers = {"X-Tt-Stage": "RELEASE", "hv5": "v5", "hv6": "v6", "hv7": "v7", "hv8": "v8", "haha": "xixi"}
   #if sys.version_info.major < 3:
   #    r.body = "特殊字符"
   #else:
   #    r.body = "特殊字符".encode("utf-8")
    sig.Sign(r)
    print("X-Tt-Timestamp: %s" % r.headers["X-Tt-Timestamp"])
    print("X-Tt-Signature-Headers: %s" % r.headers["X-Tt-Signature-Headers"])
    print("X-Tt-Signature: %s" % r.headers["X-Tt-Signature"])
    print("X-Tt-Key: %s" % r.headers["X-Tt-Key"])
    resp = requests.request(r.method, r.scheme + "://" + r.host + r.uri, headers=r.headers, data=r.body)
    print(resp.status_code, resp.reason)
    print(resp.headers)
    print(resp.content)
