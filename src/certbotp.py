"""
BSD 3-Clause License

Copyright (c) 2023, Rodolfo González González

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import time
import certbot.main
import uuid
import oss2

from rich.pretty import pprint
from OpenSSL import crypto

"""
Config must return a dictionary with at least these keys:
['OSS']['ENDPOINT'] the OSS endpoint.
['OSS']['BUCKETS']['CERTIFICATES'] the bucket where the certificate files would be stored.
['LETSENCRYPT']['DOMAINS'] lists the authorized domains.
['LETSENCRYPT']['EMAIL'] the email used for Let's Encrypt.
"""
from config import Config

###############################################################################

class Certbotp:
    # Config
    config = Config()

    # STS credentials
    keyId = os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID']
    keySecret = os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
    token = os.environ['ALIBABA_CLOUD_SECURITY_TOKEN']

    # OSS
    auth = oss2.StsAuth(keyId, keySecret, token)
    bucket = oss2.Bucket(auth,
                         config.config['OSS']['ENDPOINT'],
                         config.config['OSS']['BUCKETS']['CERTIFICATES'])

    ###########################################################################

    def getCertificate(self, domain):
        """Download the certificate from the OSS bucket.
        """
        try:
            path = "/tmp/" + uuid.uuid4().hex
            Certbotp.bucket.get_object_to_file(domain + '/cert.pem', path)

            with open(path, 'rb') as file:
                certificateData = file.read()
                return certificateData

        except Exception as ex:
            pprint(ex)
            return False
    # getCertificate

    ###########################################################################

    def provisionCertificate(self, email, domain):
        """Generates the certificate.
        """
        def uploadCertificateFile(self, path):
            """Uploads the certificate to OSS.
            """
            try:
                key = os.path.basename(os.path.dirname(path)) + \
                    '/' + os.path.basename(path)
                headers = oss2.CaseInsensitiveDict({
                    'Content-Type': "application/x-pem-file"
                })
                Certbotp.bucket.put_object_from_file(key, path, headers)

                return True

            except Exception as ex:
                pprint(ex)
                return False
        # uploadCertificateFile

        try:
            certbot.main.main([
                'certonly',                             # Obtain a cert but don't install it
                '-n',                                   # Run in non-interactive mode
                '--agree-tos',                          # Agree to the terms of service,
                '--email', email,                       # Email
                '--authenticator', 'dns-aliyun',        # Aliyun
                '--dns-aliyun-credentials', '/tmp/credentials.ini',  # Credentials
                # Override directory paths so script doesn't have to be run as root
                '--config-dir', '/tmp/config-dir/',
                '--work-dir', '/tmp/work-dir/',
                '--logs-dir', '/tmp/logs-dir/',
                '--non-interactive',
                '--break-my-certs',
                '--key-type', 'rsa',                    # RSA key
                '--force-renewal',                      # Force renewal even if not expired
                '--debug',                              # Debug messages
                '--test-cert',                          # Certificate for testing
                '-d', domain.strip()                    # Domains to provision certs for
            ])

            path = '/tmp/config-dir/live/' + domain + '/'

            r1 = uploadCertificateFile(self, path=path + 'cert.pem'),
            r2 = uploadCertificateFile(self, path=path + 'privkey.pem'),
            r3 = uploadCertificateFile(self, path=path + 'chain.pem')

            if r1 == False or r2 == False or r3 == False:
                raise Exception("Can not upload certificate to OSS for " + domain)

            return True

        except Exception as ex:
            pprint(ex)
            return False
    # provisionCertificate

    ###########################################################################

    def daysLeft(self, certificateData):
        """Calculates the days until the expiration of the certificate.
        """
        try:
            if not isinstance(certificateData, (bool, int)):
                x509 = crypto.load_certificate(
                    crypto.FILETYPE_PEM, certificateData)
                notAfter = x509.get_notAfter().decode('utf-8')

                expirationDate = time.mktime(
                    time.strptime(notAfter, '%Y%m%d%H%M%SZ'))
                currentDate = time.time()

                secondsLeft = expirationDate - currentDate
                daysLeft = secondsLeft // (24 * 60 * 60)

                return daysLeft
            else:
                return 0

        except Exception as ex:
            pprint(ex)
            return 0
    # shouldProvision

    ###########################################################################

    def setCredentials(self):
        """Sets the credentials for accessing the DNS service. Credentials are 
        passed in these enviroment variables: AUTH_ACCESSKEY_ID and
        AUTH_ACCESSKEY_SECRET
        """
        try:
            id = os.environ['AUTH_ACCESSKEY_ID']
            secret = os.environ['AUTH_ACCESSKEY_SECRET']
            token = "X"

            credentials = '''
dns_aliyun_access_key={id}
dns_aliyun_access_key_secret={secret}
dns_aliyun_access_token={token}
    '''.format(id=id, secret=secret, token=token).strip()

            with open('/tmp/credentials.ini', 'w') as f:
                f.write(credentials)
                f.close()

            os.chmod('/tmp/credentials.ini', 600)

            return True

        except Exception as ex:
            pprint(ex)
            return False
    # setCredentials

    ###########################################################################

    def certbot(self, domain):
        """Main method. Pass the domain to generate the certificate for.
        >>> myCertbot = Certbotp()
        >>> myCertbot.certbot("example.com")
        Certificate created and uploaded sucessfully
        """
        res = self.setCredentials()
        if not res:
            raise Exception("Can not set credentials")

        if domain in Certbotp.config.config['LETSENCRYPT']['DOMAINS']:
            certificate = Certbotp.getCertificate(self.bucket, domain)
            days = self.daysLeft(certificate)
            if isinstance(days, (float, int)) and days <= 15:
                print("Renewing certificate for {domain} which expires in {left} days".format(
                    domain=domain, left=days))
                res = self.provisionCertificate(self.config.config['LETSENCRYPT']['EMAIL'],
                                                domain)
                if res == True:
                    print("Certificate created and uploaded sucessfully")
            else:
                print("No renewal needed for {domain} which expires in {days} days".format(
                    domain=domain, days=days))
        else:
            raise Exception("Unknown domain " + domain)
    # certbot
# Certbot