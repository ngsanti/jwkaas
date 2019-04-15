import jwt
import logging
import json
import requests
import datetime

from .algorithms import RSAAlgorithm


class JWKaas:
    JWK_REFRESH_TIME = datetime.timedelta(hours=24)

    def __init__(self, expected_audience, expected_issuer, jwks_url=None, jwks_file=None):
        self.expected_audience = expected_audience
        self.expected_issuer = expected_issuer
        self.jwks_url = jwks_url
        self.jwks_file = jwks_file
        self.pubkeys = {}
        self.__refresh_pubkeys_cache()

    def __refresh_pubkeys_cache(self):
        self.pubkeys.clear()
        if self.jwks_file:
            self.pubkeys.update(self.__get_pubkeys_from_file(self.jwks_file))
        if self.jwks_url:
            self.pubkeys.update(self.__get_pubkeys_from_url(self.jwks_url))
        self.last_pubkeys_refresh = datetime.datetime.utcnow()

    def __get_pubkeys_from_file(self, jwks_file):
        file = open(jwks_file, 'r')
        return self.__get_pupkeys_from_json(json.loads(file.read()))

    def __get_pubkeys_from_url(self, jwks_url):
        pubkeys_json = requests.get(self.jwks_url).json()
        return self.__get_pubkeys_from_json(pubkeys_json)

    def __get_pubkeys_from_json(self, jwks_json):
        resultingkeys = {}
        if 'keys' in jwks_json:
            for key in jwks_json['keys']:
                resultingkeys[key['kid']] = RSAAlgorithm.from_jwk(json.dumps(key))
        return resultingkeys

    def __get_pubkey_by_kid(self, kid):
        if (kid not in self.pubkeys) or \
           (datetime.datetime.utcnow() - self.last_pubkeys_refresh > JWKaas.JWK_REFRESH_TIME):
            self.__refresh_pubkeys_cache()
        if kid in self.pubkeys:
            return self.pubkeys[kid]
        return None

    def get_token_info(self, token):
        headers = jwt.get_unverified_header(token)
        logging.debug("Token headers [%s]", headers)

        if not 'kid' in headers:
            logging.warning("Received token but no kid specified")
            return None

        pubkey = self.__get_pubkey_by_kid(headers['kid'])
        if pubkey is None:
            logging.warning("Received token but not found matching pubkey for [%s]", headers['kid'])
            return None

        try:
            info = jwt.decode(token, pubkey, audience=self.expected_audience, issuer=self.expected_issuer)
            logging.debug("Validated token info [%s]", info)
            return info
        except ValueError:
            logging.warning("ValueError on decoding token")
        except jwt.ExpiredSignatureError:
            logging.warning("Token is expired")
        except jwt.InvalidAudienceError:
            logging.warning("Token has invalid audience, expected [%s]", self.expected_audience)
        except jwt.InvalidIssuerError:
            logging.warning("Token issuer is invalid, expected [%s]", self.expected_issuer)
        except jwt.InvalidIssuedAtError:
            logging.warning("Token has invalid issued at time")
        return None

    # Connexion expects scope key in returned dictionary, JWT specs
    def get_connexion_token_info(self, token):
        token_info = self.get_token_info(token)
        if token_info is not None and 'scope' not in token_info and 'scopes' not in token_info and 'scp' in token_info:
            # Azure AD returns scope in scp
            token_info['scope'] = token_info['scp']
        return token_info
