import sys
import hashlib
import hmac
import binascii
from datetime import datetime
import time

if sys.version_info.major < 3:
    from urllib import quote, unquote


    def hmacsha256(keyByte, message):
        return hmac.new(keyByte, message, digestmod=hashlib.sha256).digest()

    # Create a "String to Sign".
    def StringToSign(canonicalRequest, t):
        bytes = HexEncodeSHA256Hash(canonicalRequest)
        return "%s\n%s\n%s" % (Algorithm, str(t), bytes)

else:
    from urllib.parse import quote, unquote


    def hmacsha256(keyByte, message):
        return hmac.new(keyByte.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()

        
    # Create a "String to Sign".
    def StringToSign(canonicalRequest, t):
        bytes = HexEncodeSHA256Hash(canonicalRequest.encode('utf-8'))
        return "%s\n%s\n%s" % (Algorithm, str(t), bytes)


def urlencode(s):
    return quote(s, safe='~')


def findHeader(r, header):
    for k in r.headers:
        if k.lower() == header.lower():
            return r.headers[k]
    return None


# HexEncodeSHA256Hash returns hexcode of sha256
def HexEncodeSHA256Hash(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()


# HWS API Gateway Signature
class HttpRequest:
    def __init__(self):
        self.method = ""
        self.scheme = ""  # http/https
        self.host = ""  # example.com
        self.uri = ""  # /request/uri
        self.query = {}
        self.headers = {}
        self.body = ""

Algorithm = "SDK-SHA256"
HeaderXDate = "X-Tt-Timestamp"
SingedHeaders = "X-Tt-Signature-Headers"
HeaderXSign = "X-Tt-Signature"
HeaderXKey = "X-Tt-Key"


def CanonicalRequest(r, signedHeaders):
    canonicalHeaders = CanonicalHeaders(r, signedHeaders)
    return "%s\n%s\n%s\n%s\n%s" % (
        r.method, CanonicalURI(r), CanonicalQueryString(r), canonicalHeaders, ";".join(signedHeaders))


def CanonicalURI(r):
    pattens = unquote(r.uri).split('/')
    uri = []
    for v in pattens:
        uri.append(urlencode(v))
    urlpath = "/".join(uri)
    if urlpath[-1] != '/':
        urlpath = urlpath + "/"  # always end with /
    return urlpath


def CanonicalQueryString(r):
    keys = []
    for key in r.query:
        keys.append(key)
    keys.sort()
    a = []
    for key in keys:
        k = urlencode(key)
        value = r.query[key]
        if type(value) is list:
            value.sort()
            for v in value:
                kv = k + "=" + urlencode(str(v))
                a.append(kv)
        else:
            kv = k + "=" + urlencode(str(value))
            a.append(kv)
    return '&'.join(a)


def CanonicalHeaders(r, signedHeaders):
    a = []
    __headers = {}
    for key in r.headers:
        keyEncoded = key.lower()
        value = r.headers[key]
        valueEncoded = value.strip()
        __headers[keyEncoded] = valueEncoded
        if sys.version_info.major == 3:
            r.headers[key] = valueEncoded.encode("utf-8").decode('iso-8859-1')
    for key in signedHeaders:
        a.append(key + ":" + __headers[key])
    return '\n'.join(a) + "\n"


def SignedHeaders(r):
    a = []
    for key in r.headers:
        a.append(key.lower())
    a.sort()
    return a


# Create the HWS Signature.
def SignStringToSign(stringToSign, signingKey):
    return HexEncodeSHA256Hash(signingKey + stringToSign)


class SignerError(Exception):
    pass


class Signer:
    def __init__(self):
        self.Key = ""
        self.Secret = ""

    def Verify(self, r, authorization):
        if sys.version_info.major == 3 and isinstance(r.body, str):
            r.body = r.body.encode('utf-8')
        headerTime = findHeader(r, HeaderXDate)
        if headerTime is None:
            return False
        else:
            t = int(headerTime)

        signedHeaders = SignedHeaders(r)
        canonicalRequest = CanonicalRequest(r, signedHeaders)
        stringToSign = StringToSign(canonicalRequest, t)
        return authorization == SignStringToSign(stringToSign, self.Secret)

    # SignRequest set Authorization header
    def Sign(self, r):
        if sys.version_info.major == 3 and isinstance(r.body, str):
            r.body = r.body.encode('utf-8')
        headerTime = findHeader(r, HeaderXDate)
        if headerTime is None:
            t = int(time.time())
            r.headers[HeaderXDate] = str(t)
        else:
            t = int(headerTime)

        haveHost = False
        for key in r.headers:
            if key.lower() == 'host':
                haveHost = True
                break
        if not haveHost:
            r.headers["host"] = r.host
        signedHeaders = SignedHeaders(r)
        canonicalRequest = CanonicalRequest(r, signedHeaders)
        stringToSign = StringToSign(canonicalRequest, t)
        signature = SignStringToSign(stringToSign, self.Secret)
        r.headers[HeaderXKey] = self.Key
        r.headers[HeaderXSign] = signature
        r.headers[SingedHeaders] = ";".join(signedHeaders)
        r.headers["content-length"] = str(len(r.body))
        queryString = CanonicalQueryString(r)
        if queryString != "":
            r.uri = r.uri + "?" + queryString
