__author__ = 'Matt David'

import hashlib
import json
import os
import requests
import ssl
import time
import unittest

from OpenSSL import crypto

from datetime import datetime, timedelta
from ecdsa import SigningKey, curves, VerifyingKey
from ecdsa.util import sigdecode_der, sigencode_der
from flask.ext.testing import LiveServerTestCase
from OpenSSL import crypto
from Crypto.Cipher import AES

from addressimo.config import config
from addressimo.crypto import HMAC_DRBG
from addressimo.data import IdObject
from addressimo.plugin import PluginManager
from addressimo.paymentprotocol.paymentrequest_pb2 import PaymentRequest, PaymentDetails, EncryptedPaymentRequest, InvoiceRequest, X509Certificates, EncryptedInvoiceRequest, EncryptedPayment, EncryptedPaymentACK, Payment, PaymentACK, Output
from addressimo.util import LogUtil
from server import app

SENDER_CERT = '''
-----BEGIN CERTIFICATE-----
MIIEjzCCA3egAwIBAgIJAIVQlqMNwBXHMA0GCSqGSIb3DQEBCwUAMIGLMQswCQYD
VQQGEwJVUzETMBEGA1UECBMKQ2FsaWZvcm5pYTEUMBIGA1UEBxMLTG9zIEFuZ2Vs
ZXMxFTATBgNVBAoTDE5ldGtpIFNlbmRlcjEVMBMGA1UEAxMMTmV0a2kgU2VuZGVy
MSMwIQYJKoZIhvcNAQkBFhRvcGVuc291cmNlQG5ldGtpLmNvbTAeFw0xNTExMjMy
MzM2MjFaFw0yNTExMjAyMzM2MjFaMIGLMQswCQYDVQQGEwJVUzETMBEGA1UECBMK
Q2FsaWZvcm5pYTEUMBIGA1UEBxMLTG9zIEFuZ2VsZXMxFTATBgNVBAoTDE5ldGtp
IFNlbmRlcjEVMBMGA1UEAxMMTmV0a2kgU2VuZGVyMSMwIQYJKoZIhvcNAQkBFhRv
cGVuc291cmNlQG5ldGtpLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
ggEBAL96JZwop5I3kOsZFNiqWd86A+jyKU/X/xKYdwcMq9Sto4dYXWIh3vUKZVZX
y6P9kZhQ0RX2jlqN1uEijpD3JDkTpEQzyAEcH3PBG7R/BH9xVyWhitBCnW3Wv44d
GOOwYkvaY5BSTos4Kkowao2LxWhLYnPUMc9jwiNX0EWFE2ltPMb6404mINtuqVnz
Cp5b2sS7Xk0CnC1GsHVH/pc1/9ec2CVWVGxZ10aBCeWVtBOz0O5DBMRNaBbYYGr4
aLjS/1EFs1Gk2DpfdHWEmERtiTmt5K3bgn+CnpdQAxI5REhRsmAhvugDuohdlUQp
mbRCGM4SXntseX/R3HonEM2Lz88CAwEAAaOB8zCB8DAdBgNVHQ4EFgQUSrzo15NC
vWnKvQ3k9ckWnNsmbk4wgcAGA1UdIwSBuDCBtYAUSrzo15NCvWnKvQ3k9ckWnNsm
bk6hgZGkgY4wgYsxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRQw
EgYDVQQHEwtMb3MgQW5nZWxlczEVMBMGA1UEChMMTmV0a2kgU2VuZGVyMRUwEwYD
VQQDEwxOZXRraSBTZW5kZXIxIzAhBgkqhkiG9w0BCQEWFG9wZW5zb3VyY2VAbmV0
a2kuY29tggkAhVCWow3AFccwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOC
AQEAsdzjZv2D8ufZ2wDUS9n1I+70Zhs792/lpKK6ml1b6goie12nBE6R3g4ljLiw
yxSDRV24gzRq4YMn6OZIsvrW8D/hk3tMVKPx94etImnRCw3Z6pDyl/Bhca6alC7X
fPmTc32vjiKsf3I0yauz4IhS4P/vuQdkVAVj6o29hy84C5kRrFsdP1/aR6RDKxCJ
D3/lKhBf9K0we7bljjBwdIu6DS4DfbL/tm9CnrMz7EdkaZtoZXLOi1uRYTyWoyY8
sO2reNRhJ8m9Pvhg5lxURwDz8VgTMA6nc+2854DClXWTfqK7HsdfNq4BXn9sOwPO
gKJacJl27b+w1/V04aZ+xFgwXQ==
-----END CERTIFICATE-----
'''

SENDER_CERT_PRIVKEY = '''
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAv3olnCinkjeQ6xkU2KpZ3zoD6PIpT9f/Eph3Bwyr1K2jh1hd
YiHe9QplVlfLo/2RmFDRFfaOWo3W4SKOkPckOROkRDPIARwfc8EbtH8Ef3FXJaGK
0EKdbda/jh0Y47BiS9pjkFJOizgqSjBqjYvFaEtic9Qxz2PCI1fQRYUTaW08xvrj
TiYg226pWfMKnlvaxLteTQKcLUawdUf+lzX/15zYJVZUbFnXRoEJ5ZW0E7PQ7kME
xE1oFthgavhouNL/UQWzUaTYOl90dYSYRG2JOa3krduCf4Kel1ADEjlESFGyYCG+
6AO6iF2VRCmZtEIYzhJee2x5f9HceicQzYvPzwIDAQABAoIBABIdRCGZ1wCGMTeM
j+RPeWEc4/HNtwrOrFreAaSxFjBwnN/ZBDycZ7NW4G9iruk8u+FlA+LICH+Ym5OA
6WvddZfQu+GX5Hv2ZSNWSYCx44MK/euZdMBvDOWvQz/2kLw5m5MBfhnRL40MKzQJ
kIsDhhFv0EiU8oFkNqGRVSq+hC+c9BO+cCTSrgZ0fSkZJnx80IZFd2/IZTBxgsnX
F0vGPDY/VLRgOC8paT4pcR3PxW0ZlSEoiW7B3rztpZynY9g7wnkrHamlYH9mHret
jNx49gAs3gW02FeNt0cJOtfxe+3u8no8zFPZeb0ca6GfshNMdtScFqeJCtGVoD/W
IJo//QECgYEA4tlHJpNCRDJQ+VDA26Hq/pKh2LBQbvcEeFfQQZDY3eMFetyLysgh
1ZFSYqz3NAgsXPOTfmk2z0D9SEhHVS/h9DaIb3dhIdpSGvrbiXBnC22sJ9G7qwBZ
hh/NsBqZHuuf+9hHPELAerHNxjlc2CRKC39yZ7MeLAjCg/yI+lBXz1ECgYEA2BU8
qRs6SfNVsXTzcHzM0C06UYjiMsr1Ht9KG2D5YDOJXnPcL9G8x5auhJFwc585Z6Tl
68tC9rJUjFBmZx9BMzMIYQ3/6GMVBlQqr/EvBNoXnQrpa0yzjItOt1Y/3LcVdBZA
o6asuMtoI69+USEKdk4si/BJlLTP2RdI2LQDJR8CgYAumcIDC6dGSSvXO56Sv919
dHPpBrdPRFFXw3pVrcLPOi7LAXl6K8i/jb3l5XBW8QLkCWmYQ1buFoSxj5+PwWli
eL1oYJbElIvfXP8yabPRZjNCbtRlmYnKgsgHUD96WZ8g5loj5/aQfewut2P6RuIr
IIBJC0O8egQzhvJAsbaIMQKBgAyU7/tIwpQbvxmeHa6nFaXpfEPTHJioiK1Lgx0l
AGBBn/YH+QIvzDYy5+aAMXQKCWWnjFu2cie7KoEhDVVj1IAOsKY2EniNjGPZ8sJb
4Mj/ifBy+jRtOucsFWFHfGB1qKIhyZG92sDH10B8r3Y53koVMzLSwvYNsSyK1osH
sEcxAoGBAJDHBlIFSWwkDX/fV1H1VeX1vYi+Idi5iHkM3yTC52Yc6ilNs1KmbCx4
VLEc0GeytAzZecOdrQH5XGjWjqi3RDjxsp52yfL8xWkcKgMmdfBIAsSKNrl5ih6c
UYQnomt1/nv3xH9Q93gV4j0OF+G4IguID62mrqCq72Ca7i6TgnON
-----END RSA PRIVATE KEY-----
'''

RECEIVER_CERT = '''
-----BEGIN CERTIFICATE-----
MIIDjjCCAnYCCQCEYiGXmolUUjANBgkqhkiG9w0BAQsFADCBiDELMAkGA1UEBhMC
VVMxEzARBgNVBAgMCkNhbGlmb3JuaWExFDASBgNVBAcMC0xvcyBBbmdlbGVzMRQw
EgYDVQQKDAtOZXRraSwgSW5jLjETMBEGA1UEAwwKYWRkcmVzc2ltbzEjMCEGCSqG
SIb3DQEJARYUb3BlbnNvdXJjZUBuZXRraS5jb20wHhcNMTUwNzA2MTc0NzU3WhcN
MTYwNzA1MTc0NzU3WjCBiDELMAkGA1UEBhMCVVMxEzARBgNVBAgMCkNhbGlmb3Ju
aWExFDASBgNVBAcMC0xvcyBBbmdlbGVzMRQwEgYDVQQKDAtOZXRraSwgSW5jLjET
MBEGA1UEAwwKYWRkcmVzc2ltbzEjMCEGCSqGSIb3DQEJARYUb3BlbnNvdXJjZUBu
ZXRraS5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQD0mXwQNo1t
+mWmUBOvzQu9c3dNc019NL22MhjQtj5xtloSURpKJEDnkSH9QmiKmwCmCP534fpe
EjjTMnssa211j9CrRjGhlw2utj758+0+fWxNcaw2axBqFaLTZ08kI9325kOmMqj3
ZihzGKl9k6TTa+F/yYBsUg9gWM8R2Kx+TPhDWd2F2qtYEsJ/+FuSmbTbhVK1xyKw
xt6pgnLuON7n012rDzFpWp6xhpnxdwJKT618I6EvzgImQQXwrHcaxMfsYvbIx3t6
WadNwe3DV0onmlP2HWgrZjqlSyZkJtbJNt9M9UNPvHpan2nhM+uFFNYm7Lds3HWn
E80Erde6DUFnAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAO7HuYR3eDQtJfvmqF9z
whduPlI2tcuQaC5qnAuw9QACJ1P7f/JgjBa4ZdUp3ll0Ka9H4XK+zdh9FE8NGSXX
2kOdkJvw3S9rKacXkFKfDqbHOURyrXZ5Qnd7gn9UjStrt7nULYQR2CnND018MXT2
ojK1hGJt5Hh7jGwjKvPQe8Xb4i6u36zOQMNk7t7x+ryhoUxtX5uiiJFOt9ZsTsbn
RmkGxmG3vqq0S4yqClEG8MbRU4XVSu73OL+WM8Eo7eTltHirP81CztR8ki6WrD5W
VaTgdpiY90zRckz8wdX1WsAZs4xOL4ECxdDU9puvwDBWME4Ijt9PRSlzwsukv08B
yfk=
-----END CERTIFICATE-----
'''

RECEIVER_CERT_PRIVKEY = '''
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA9Jl8EDaNbfplplATr80LvXN3TXNNfTS9tjIY0LY+cbZaElEa
SiRA55Eh/UJoipsApgj+d+H6XhI40zJ7LGttdY/Qq0YxoZcNrrY++fPtPn1sTXGs
NmsQahWi02dPJCPd9uZDpjKo92YocxipfZOk02vhf8mAbFIPYFjPEdisfkz4Q1nd
hdqrWBLCf/hbkpm024VStccisMbeqYJy7jje59Ndqw8xaVqesYaZ8XcCSk+tfCOh
L84CJkEF8Kx3GsTH7GL2yMd7elmnTcHtw1dKJ5pT9h1oK2Y6pUsmZCbWyTbfTPVD
T7x6Wp9p4TPrhRTWJuy3bNx1pxPNBK3Xug1BZwIDAQABAoIBAQDZvRf3xtg3osOC
PZ6IzNs6luMJCy9b2etXmVkF0nXb/BxKWfAxN/yfJ08+iDNPz5PQOgls5rldrJLx
TurfK/KQyKlVDnN4CWOgt5NwJnh3PGeAuUQ4XS6LgR8lWb3Vyif5dhmahVZshYBU
lQusQhZkLpDalKHBy3rspaIPnPZQpq6FwGuLoOb469Evv1HdXT1CsSQKoPnQaWnv
l1IwYAOtbsQOYIL3xqEpMXqMwFOx/5V4qzCkrgZYhRTlJ5MJJgNZ60EswP6cm9AG
PIoYtelqQiYVlcLXc4fSLzT7QN94ncX5Qf0Xs0hDpCENxJsiiHzIARa3dz7C+fx9
lPpROW/hAoGBAPpyLukh24j4Hc+RD9dSt02ISFaeeI98EvwesEl73HFTB5w9QrA6
dLIG4cT7RHMI3vUMj/BUN3cyEMCRyibdnulAmoQhvBy6dSMnRKdbHmdXCKEA8Nkx
JSYcgFgPP6hqMDVtC2jmkERb8UTjIXQyN5ly1HSWaVtd0bMcthlYGJS9AoGBAPoG
HC//eQYAmcFwDkO08ckS+AKEJOdqZgNBW/CCKn3YiXi9adrbRaaHSDEr7hGSM5aT
jmJh0PGJKELMVoa3zHTQQ0PgKuWUQ7wLnUV4qy1XSOiCyVnk5nYDHknNF8n7sTUs
foc5IWYcQQ3VKwSNmIXgdW8nnsxPJwm1D0gfjnrzAoGBANxMdFc+IQ5qsk5TG8wc
RoE8z+ThoMsWKNz9YbRB77b/gkI84NyDjwLKau4K2DsYIocLddHBQsjmkTXTCC8H
4zDqUwDHa+EZYtB5SjqsPCJKvJxjZ3ilcjgD+iF7yFMslRtpwA+WQHDhL2mZIWRE
iAPCrn+fjy1/aWZUaxoAFB9BAoGAafobCpFMOCobAi5ALZzN+7/plg9zIRAta2XR
1bEm167oHmCTNOxKqpqfFBCd2Z7R9RpYeQUjLq5HfYDlkDbqF/2K9YNYS3W7/EIk
CKVsUUy1H7EILe1jblRGC1w+oCPqajKQ8zpZGNITFQztLgHiy6RnwpTVr55BWtD/
SD/wAdcCgYBUMjnggyFXCBlatQwJ0x0kvSts9ssoYAHPjnrM6E4PpG9okSrlCBQ0
zSc+dbwv1qsO2j4i2PlHShMSoR/Vrv+69a9d6S2D2hZzl6L/B4Na+250xdyHyfGS
TWeo5LnGCgNnyl/Mfte1mYjJLJ/A1QAK/NEpddrF2TNMzOiVw9cBWQ==
-----END RSA PRIVATE KEY-----
'''

log = LogUtil.setup_logging()

# Crypto Utility Functions
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]

class BIP75FunctionalTest(LiveServerTestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['LIVESERVER_PORT'] = 47294
        app.config['DEBUG'] = True
        return app

    @classmethod
    def setUpClass(cls):

        log.info('Generating ECDSA Keypairs for Testing')
        cls.sender_sk = SigningKey.generate(curve=curves.SECP256k1)
        cls.receiver_sk = SigningKey.generate(curve=curves.SECP256k1)

        log.info('Setup IdObj for testid')
        cls.test_id_obj = IdObject()
        cls.test_id_obj.auth_public_key = cls.receiver_sk.get_verifying_key().to_der().encode('hex')
        cls.test_id_obj.id = 'testid'
        cls.test_id_obj.ir_only = True

        cls.resolver = PluginManager.get_plugin('RESOLVER', config.resolver_type)
        cls.resolver.save(cls.test_id_obj)
        log.info('Save testid IdObj')

    @classmethod
    def tearDownClass(cls):

        time.sleep(1)

        resolver = PluginManager.get_plugin('RESOLVER', config.resolver_type)
        log.info('Clean Up Functest')

        log.info('Deleting All testid InvoiceRequests if any exist')
        for ir in resolver.get_invoicerequests('testid'):
            log.info('Deleting InvoiceRequest [ID: %s]' % ir.get('id'))
            resolver.delete_invoicerequest('testid', ir.get('id'))

        log.info('Deleting Test IdObj')
        resolver.delete(BIP75FunctionalTest.test_id_obj)

    def ecdh_encrypt(self, plaintext, nonce, pubkey, privkey):

        ecdh_point = privkey.privkey.secret_multiplier * pubkey.pubkey.point
        log.debug('ECDH_POINT: %s' % ecdh_point.x())

        # Encrypt PR using HMAC-DRBG
        drbg = HMAC_DRBG(entropy=str(ecdh_point.x()), nonce=str(nonce))
        encryption_key = drbg.generate(32)
        iv = drbg.generate(16)
        encrypt_obj = AES.new(encryption_key, AES.MODE_CBC, iv)
        ciphertext = encrypt_obj.encrypt(pad(plaintext))
        return ciphertext

    def ecdh_decrypt(self, ciphertext, nonce, pubkey, privkey):

        ecdh_point = privkey.privkey.secret_multiplier * pubkey.pubkey.point
        log.debug('ECDH_POINT: %s' % ecdh_point.x())

        # Encrypt PR using HMAC-DRBG
        drbg = HMAC_DRBG(entropy=str(ecdh_point.x()), nonce=str(nonce))
        encryption_key = drbg.generate(32)
        iv = drbg.generate(16)
        encrypt_obj = AES.new(encryption_key, AES.MODE_CBC, iv)
        plaintext = unpad(encrypt_obj.decrypt(ciphertext))
        return plaintext

    def test_bip75_flow(self):

        ###################
        # Load Crypto Keys
        ###################
        self.x509_sender_cert = crypto.load_certificate(crypto.FILETYPE_PEM, SENDER_CERT)
        self.x509_sender_cert_privkey = crypto.load_privatekey(crypto.FILETYPE_PEM, SENDER_CERT_PRIVKEY)

        self.x509_receiver_cert = crypto.load_certificate(crypto.FILETYPE_PEM, RECEIVER_CERT)
        self.x509_receiver_cert_privkey = crypto.load_privatekey(crypto.FILETYPE_PEM, RECEIVER_CERT_PRIVKEY)

        #########################
        # Create InvoiceRequest
        #########################
        log.info("Building InvoiceRequest")

        self.request_nonce = int(time.time() * 1000000)
        invoice_request = InvoiceRequest()
        invoice_request.sender_public_key = BIP75FunctionalTest.sender_sk.get_verifying_key().to_der()
        invoice_request.amount = 75
        invoice_request.pki_type = 'x509+sha256'

        sender_certs = X509Certificates()
        sender_certs.certificate.append(ssl.PEM_cert_to_DER_cert(crypto.dump_certificate(crypto.FILETYPE_PEM, self.x509_sender_cert)))
        invoice_request.pki_data = sender_certs.SerializeToString()
        invoice_request.notification_url = 'https://notify.me/longId'
        invoice_request.signature = ""

        # Handle x509 Signature
        sig = crypto.sign(self.x509_sender_cert_privkey, invoice_request.SerializeToString(), 'sha1')
        invoice_request.signature = sig

        ##################################
        # Create EncryptedInvoiceRequest
        ##################################
        ciphertext = self.ecdh_encrypt(
            plaintext=invoice_request.SerializeToString(),
            nonce=self.request_nonce,
            pubkey=BIP75FunctionalTest.receiver_sk.get_verifying_key(),
            privkey=BIP75FunctionalTest.sender_sk
        )

        eir = EncryptedInvoiceRequest()
        eir.sender_public_key = BIP75FunctionalTest.sender_sk.get_verifying_key().to_der()
        eir.receiver_public_key = BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der()
        eir.nonce = self.request_nonce
        eir.encrypted_invoice_request = ciphertext
        eir.invoice_request_hash = hashlib.sha256(invoice_request.SerializeToString()).digest()
        eir.signature = ''
        eir.signature = BIP75FunctionalTest.sender_sk.sign(eir.SerializeToString(), hashfunc=hashlib.sha256, sigencode=sigencode_der)

        #############################
        # Sign & Submit HTTP Request
        #############################
        post_url = "%s/address/testid/resolve" % self.get_server_url()
        msg_sig = BIP75FunctionalTest.sender_sk.sign(post_url + eir.SerializeToString())

        ir_headers = {
            'X-Identity': BIP75FunctionalTest.sender_sk.get_verifying_key().to_der().encode('hex'),
            'X-Signature': msg_sig.encode('hex'),
            'Content-Type': 'application/bitcoin-encrypted-invoicerequest',
            'Content-Transfer-Encoding': 'binary'
        }
        log.info("Submitting EncryptedInvoiceRequest")
        response = requests.post(post_url, headers=ir_headers, data=eir.SerializeToString())

        # Validate Response
        self.assertEqual(202, response.status_code)
        self.assertTrue(response.headers.get('Location').startswith('https://%s/encryptedpaymentrequest' % config.site_url))
        self.payment_id = response.headers.get('Location').rsplit('/', 1)[1]

        log.info('Payment ID: %s' % self.payment_id)

        ######################################
        # Get InvoiceRequests from Addressimo
        ######################################
        sign_url = "%s/address/testid/invoicerequests" % self.get_server_url()
        msg_sig = BIP75FunctionalTest.receiver_sk.sign(sign_url)

        ir_req_headers = {
            'X-Identity': BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der().encode('hex'),
            'X-Signature': msg_sig.encode('hex')
        }

        log.info("Retrieving EncryptedInvoiceRequests")
        response = requests.get(sign_url, headers=ir_req_headers)

        log.info("EncryptedInvoiceRequest Retrieval Response [CODE: %d | TEXT: %s]" % (response.status_code, response.text))
        self.assertEqual(200, response.status_code)
        self.assertIsNotNone(response.text)

        ###############################################
        # Retrieve and Decrypt EncryptedInvoiceRequest
        ###############################################
        received_eir = EncryptedInvoiceRequest()
        try:
            resp_json = response.json()
            received_eir.ParseFromString(resp_json.get('requests')[0].get('encrypted_invoice_request','').decode('hex'))
        except Exception as e:
            self.fail("Exception while parsing EncryptedInvoiceRequest: %s" % str(e))

        # Determine ECDH Shared Key
        sender_vk = VerifyingKey.from_der(received_eir.sender_public_key)
        self.assertEqual(received_eir.receiver_public_key, BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der())

        decrypt_ciphertext = self.ecdh_decrypt(
            ciphertext=received_eir.encrypted_invoice_request,
            nonce=received_eir.nonce,
            pubkey=sender_vk,
            privkey=BIP75FunctionalTest.receiver_sk
        )

        received_invoice_request = InvoiceRequest()
        try:
            received_invoice_request.ParseFromString(decrypt_ciphertext)
            self.assertEqual(received_eir.invoice_request_hash, hashlib.sha256(received_invoice_request.SerializeToString()).digest())
            log.info("Successfully Retrieved and Parsed an InvoiceRequest")
        except Exception as e:
            self.fail("Exception while parsing InvoiceRequest: %s" % str(e))

        #######################
        # Create EPR
        #######################
        log.info("Building EncryptedPaymentRequest")
        pd = PaymentDetails()
        pd.network = 'main'
        output = pd.outputs.add()
        output.amount = received_invoice_request.amount
        output.script = 'paymesomemoneyhere'.encode('hex')
        pd.time = int(datetime.utcnow().strftime('%s'))
        pd.expires = int((datetime.utcnow() + timedelta(seconds=3600)).strftime('%s'))
        pd.memo = ''
        pd.payment_url = ''
        pd.merchant_data = ''

        pr = PaymentRequest()
        pr.payment_details_version = 1
        pr.pki_type = 'none'
        pr.pki_data = ''
        pr.serialized_payment_details = pd.SerializeToString()
        pr.signature = 'testforme'

        self.serialized_pr = pr.SerializeToString()

        # Encrypt PaymentRequest
        next_nonce = int(time.time() * 1000000)
        ciphertext = self.ecdh_encrypt(
            plaintext=self.serialized_pr,
            nonce=next_nonce,
            pubkey=VerifyingKey.from_der(received_invoice_request.sender_public_key),
            privkey=BIP75FunctionalTest.receiver_sk
        )

        self.assertEqual(self.payment_id, resp_json.get('requests')[0]['id'])

        # Create EncryptedPaymentRequest
        epr = EncryptedPaymentRequest()
        epr.encrypted_payment_request = ciphertext
        epr.receiver_public_key = received_eir.receiver_public_key
        epr.sender_public_key = received_eir.sender_public_key
        epr.payment_request_hash = hashlib.sha256(self.serialized_pr).digest()
        epr.nonce = next_nonce
        epr.signature = ''
        epr.signature = BIP75FunctionalTest.receiver_sk.sign(epr.SerializeToString(), hashfunc=hashlib.sha256, sigencode=sigencode_der)

        submit_rpr_data = {
            "ready_requests": [
                {
                    "id": resp_json.get('requests')[0].get('id'),
                    "encrypted_payment_request": epr.SerializeToString().encode('hex')
                }
            ]
        }

        sign_url = "%s/address/testid/invoicerequests" % self.get_server_url()
        msg_sig = BIP75FunctionalTest.receiver_sk.sign(sign_url + json.dumps(submit_rpr_data))

        ir_req_headers = {
            'X-Identity': BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der().encode('hex'),
            'X-Signature': msg_sig.encode('hex'),
            'Content-Type': 'application/json'
        }

        log.info("Submitting EncryptedPaymentRequest")
        response = requests.post(sign_url, data=json.dumps(submit_rpr_data), headers=ir_req_headers)
        log.info('SubmitEPR Response: %s' % response.text)
        self.assertEqual(200, response.status_code)

        # Verify the InvoiceRequest was deleted after submission occurred
        for ir in self.resolver.get_invoicerequests('testid'):
            self.assertFalse(ir['id'] == resp_json.get('requests')[0]['id'])

        # Make Sure One RPR Was Accepted
        resp_json = response.json()
        self.assertEqual(1, resp_json['ready_accept_count'])

        #######################
        # Retrieve EncryptedPaymentRequest
        #######################
        log.info("Retrieving EncryptedPaymentRequest")
        sign_url = "%s/encryptedpaymentrequest/%s" % (self.get_server_url(), self.payment_id)
        response = requests.get(sign_url)
        self.assertIsNotNone(response)

        self.assertIn('Content-Transfer-Encoding', response.headers)
        self.assertEqual('binary', response.headers.get('Content-Transfer-Encoding'))
        self.assertIn('Content-Type', response.headers)
        self.assertEqual('application/bitcoin-encrypted-paymentrequest', response.headers.get('Content-Type'))

        returned_pr = EncryptedPaymentRequest()
        try:
            returned_pr.ParseFromString(response.content)
            log.info("EncryptedPaymentRequest Parsed")
        except Exception as e:
            self.fail('Unable to Parse EncryptedPaymentRequest')

        log.info('Received EncryptedPaymentRequest')

        self.assertEqual(BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der(), returned_pr.receiver_public_key)
        self.assertEqual(BIP75FunctionalTest.sender_sk.get_verifying_key().to_der(), returned_pr.sender_public_key)
        self.assertEqual(ciphertext, returned_pr.encrypted_payment_request)

        # Decrypt Response
        decrypt_ciphertext = self.ecdh_decrypt(
            ciphertext=returned_pr.encrypted_payment_request,
            nonce=returned_pr.nonce,
            pubkey=VerifyingKey.from_der(returned_pr.receiver_public_key),
            privkey=BIP75FunctionalTest.sender_sk
        )
        self.assertEqual(self.serialized_pr, decrypt_ciphertext)
        log.info("Decrypted Text Matches Initial Serialized PaymentRequest")

        rpr = PaymentRequest()
        rpr.ParseFromString(decrypt_ciphertext)
        self.assertEqual(1, rpr.payment_details_version)
        self.assertEqual('none', rpr.pki_type)
        self.assertEqual('', rpr.pki_data)
        self.assertEqual(pd.SerializeToString(), rpr.serialized_payment_details)
        self.assertEqual('testforme', rpr.signature)

        # Authenticate PR Hash
        self.assertEqual(hashlib.sha256(decrypt_ciphertext).digest(), returned_pr.payment_request_hash)
        log.info("PaymentRequest SHA256 Hash Matches EncryptedPaymentRequest's Payment Request Hash")

        #######################################
        # Create / Submit (Encrypted)Payment
        #######################################
        payment = Payment()
        payment.merchant_data = 'nodusttxs'.encode('hex')
        payment.transactions.append('btc_tx'.encode('hex'))
        out = payment.refund_to.add()
        out.script = 'myp2shaddress'.encode('hex')

        encrypted_payment = EncryptedPayment()
        encrypted_payment.nonce = int(time.time() * 1000000)
        encrypted_payment.sender_public_key = returned_pr.sender_public_key
        encrypted_payment.receiver_public_key = returned_pr.receiver_public_key
        encrypted_payment.payment_hash = hashlib.sha256(payment.SerializeToString()).digest()
        encrypted_payment.encrypted_payment = self.ecdh_encrypt(
            plaintext=payment.SerializeToString(),
            nonce=encrypted_payment.nonce,
            pubkey=VerifyingKey.from_der(encrypted_payment.receiver_public_key),
            privkey=BIP75FunctionalTest.sender_sk
        )
        encrypted_payment.signature = ''
        encrypted_payment.signature = BIP75FunctionalTest.sender_sk.sign(encrypted_payment.SerializeToString(), hashfunc=hashlib.sha256, sigencode=sigencode_der)

        # Submit EncryptedPayment
        sign_url = "%s/payment/%s" % (self.get_server_url(), self.payment_id)
        msg_sig = BIP75FunctionalTest.sender_sk.sign(sign_url + encrypted_payment.SerializeToString())

        ep_req_headers = {
            'X-Identity': BIP75FunctionalTest.sender_sk.get_verifying_key().to_der().encode('hex'),
            'X-Signature': msg_sig.encode('hex'),
            'Content-Type': 'application/bitcoin-encrypted-payment',
            'Content-Transfer-Encoding': 'binary'
        }

        log.info("Submitting EncryptedPayment")
        response = requests.post(sign_url, data=encrypted_payment.SerializeToString(), headers=ep_req_headers)
        log.info('Submit EncryptedPayment Response: %s' % response.text)
        self.assertEqual(200, response.status_code)

        #######################
        # Retrieve EncryptedPayment
        #######################
        log.info("Retrieving EncryptedPayment")
        sign_url = "%s/payment/%s" % (self.get_server_url(), self.payment_id)
        response = requests.get(sign_url)
        self.assertIsNotNone(response)

        self.assertIn('Content-Transfer-Encoding', response.headers)
        self.assertEqual('binary', response.headers.get('Content-Transfer-Encoding'))
        self.assertIn('Content-Type', response.headers)
        self.assertEqual('application/bitcoin-encrypted-payment', response.headers.get('Content-Type'))

        returned_ep = EncryptedPayment()
        try:
            returned_ep.ParseFromString(response.content)
            log.info("EncryptedPayment Parsed")
        except Exception as e:
            self.fail('Unable to Parse EncryptedPayment')

        log.info('Received EncryptedPayment')

        self.assertEqual(BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der(), returned_ep.receiver_public_key)
        self.assertEqual(BIP75FunctionalTest.sender_sk.get_verifying_key().to_der(), returned_ep.sender_public_key)
        self.assertEqual(encrypted_payment.encrypted_payment, returned_ep.encrypted_payment)

        # Decrypt Response
        decrypt_ciphertext = self.ecdh_decrypt(
            ciphertext=returned_ep.encrypted_payment,
            nonce=returned_ep.nonce,
            pubkey=VerifyingKey.from_der(returned_ep.sender_public_key),
            privkey=BIP75FunctionalTest.receiver_sk
        )

        payment_msg = Payment()
        payment_msg.ParseFromString(decrypt_ciphertext)
        self.assertEqual('nodusttxs'.encode('hex'), payment_msg.merchant_data)
        self.assertEqual(1, len(payment_msg.transactions))
        self.assertEqual('btc_tx'.encode('hex'), payment_msg.transactions[0])

        # Authenticate PR Hash
        self.assertEqual(hashlib.sha256(decrypt_ciphertext).digest(), returned_ep.payment_hash)
        log.info("EncryptedPayment SHA256 Hash Matches EncryptedPayment's Payment Hash")

        #######################################
        # Create / Submit (Encrypted)PaymentACK
        #######################################
        paymentack = PaymentACK()
        paymentack.payment.CopyFrom(payment_msg)
        paymentack.memo = 'Payment ACKed'

        encrypted_paymentack = EncryptedPaymentACK()
        encrypted_paymentack.nonce = int(time.time() * 1000000)
        encrypted_paymentack.sender_public_key = epr.sender_public_key
        encrypted_paymentack.receiver_public_key = epr.receiver_public_key
        encrypted_paymentack.payment_ack_hash = hashlib.sha256(paymentack.SerializeToString()).digest()
        encrypted_paymentack.encrypted_payment_ack = self.ecdh_encrypt(
            plaintext=paymentack.SerializeToString(),
            nonce=encrypted_paymentack.nonce,
            pubkey=VerifyingKey.from_der(encrypted_paymentack.sender_public_key),
            privkey=BIP75FunctionalTest.receiver_sk
        )
        encrypted_paymentack.signature = ''
        encrypted_paymentack.signature = BIP75FunctionalTest.receiver_sk.sign(encrypted_paymentack.SerializeToString(), hashfunc=hashlib.sha256, sigencode=sigencode_der)

        # Submit EncryptedPaymentAck
        sign_url = "%s/paymentack/%s" % (self.get_server_url(), self.payment_id)
        msg_sig = BIP75FunctionalTest.receiver_sk.sign(sign_url + encrypted_paymentack.SerializeToString())

        ep_req_headers = {
            'X-Identity': BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der().encode('hex'),
            'X-Signature': msg_sig.encode('hex'),
            'Content-Type': 'application/bitcoin-encrypted-paymentack',
            'Content-Transfer-Encoding': 'binary'
        }

        log.info("Submitting EncryptedPaymentAck")
        response = requests.post(sign_url, data=encrypted_paymentack.SerializeToString(), headers=ep_req_headers)
        log.info('Submit EncryptedPaymentAck Response: %s' % response.text)
        self.assertEqual(200, response.status_code)

        ###############################
        # Retrieve EncryptedPaymentAck
        ###############################
        log.info("Retrieving EncryptedPaymentAck")
        sign_url = "%s/paymentack/%s" % (self.get_server_url(), self.payment_id)
        response = requests.get(sign_url)
        self.assertIsNotNone(response)

        self.assertIn('Content-Transfer-Encoding', response.headers)
        self.assertEqual('binary', response.headers.get('Content-Transfer-Encoding'))
        self.assertIn('Content-Type', response.headers)
        self.assertEqual('application/bitcoin-encrypted-paymentack', response.headers.get('Content-Type'))

        returned_epa = EncryptedPaymentACK()
        try:
            returned_epa.ParseFromString(response.content)
            log.info("EncryptedPaymentACK Parsed")
        except Exception as e:
            self.fail('Unable to Parse EncryptedPaymentACK')

        log.info('Received EncryptedPaymentACK')

        self.assertEqual(BIP75FunctionalTest.receiver_sk.get_verifying_key().to_der(), returned_ep.receiver_public_key)
        self.assertEqual(BIP75FunctionalTest.sender_sk.get_verifying_key().to_der(), returned_ep.sender_public_key)
        self.assertEqual(encrypted_paymentack.encrypted_payment_ack, returned_epa.encrypted_payment_ack)

        # Decrypt Response
        decrypt_ciphertext = self.ecdh_decrypt(
            ciphertext=returned_epa.encrypted_payment_ack,
            nonce=returned_epa.nonce,
            pubkey=VerifyingKey.from_der(returned_epa.receiver_public_key),
            privkey=BIP75FunctionalTest.sender_sk
        )

        paymentack_msg = PaymentACK()
        paymentack_msg.ParseFromString(decrypt_ciphertext)

        # Authenticate PR Hash
        self.assertEqual(hashlib.sha256(decrypt_ciphertext).digest(), returned_epa.payment_ack_hash)
        log.info("EncryptedPaymentAck SHA256 Hash Matches EncryptedPaymentAck's PaymentAck Hash")

if __name__ == '__main__':

    unittest.main()