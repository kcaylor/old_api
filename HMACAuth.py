from eve import Eve
from flask import request
from eve.auth import HMACAuth
from hashlib import sha1
import base64
import hmac
from hashlib import sha1
from pulsepod.compat import izip
from pulsepod.utils import cfg

class HMACAuth(HMACAuth):

    def __init__(self):
        self.token = cfg.API_AUTH_TOKEN

    def compute_signature(self, uri, data):
        """Compute the signature for a given request

        :param uri: full URI for request on API
        :param params: post vars sent with the request
        
        :returns: The computed signature
        """
        s = uri
        if len(data) > 0:
            s += data

        # compute signature and compare signatures
        mac = hmac.new(self.token, s.encode("utf-8"), sha1)
        computed = base64.b64encode(mac.digest())

        return computed.strip()

    def check_auth(self, userid, uri, data, hmac_hash, resource, method):
        if method in ['GET','HEAD','OPTIONS']:
            return True
        else:
            return self.validate(uri, data, hmac_hash)

    def validate(self, uri, data, signature):
        """Validate a request from Twilio

        :param uri: full URI that was requested on your server
        :param params: post vars that were sent with the request
        :param signature: expexcted signature in HTTP Authorization header
        :param auth: tuple with (account_sid, token)

        :returns: True if the request passes validation, False if not
        """
        return secure_compare(self.compute_signature(uri, data), signature)


    def authorized(self, allowed_roles, resource, method):
        """ Validates the the current request is allowed to pass through.

        :param allowed_roles: allowed roles for the current request, can be a
                              string or a list of roles.
        :param resource: resource being requested.
        """
        auth = request.headers.get('Authorization')
        try:
            userid, hmac_hash = auth.split(':')
        except:
            auth = None
        return auth and self.check_auth(userid, request.url, request.get_data(), \
                            hmac_hash, resource, method )


def secure_compare(string1, string2):
    """Compare two strings while protecting against timing attacks

    :param str string1: the first string
    :param str string2: the second string

    :returns: True if the strings are equal, False if not
    :rtype: :obj:`bool`
    """
    if len(string1) != len(string2):
        return False
    result = True
    for c1, c2 in izip(string1, string2):
        result &= c1 == c2
    return result
