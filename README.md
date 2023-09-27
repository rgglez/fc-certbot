# fc-certbot

[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause) 
![GitHub all releases](https://img.shields.io/github/downloads/rgglez/fc-certbot/total) 
![GitHub issues](https://img.shields.io/github/issues/rgglez/fc-certbot) 
![GitHub commit activity](https://img.shields.io/github/commit-activity/y/rgglez/fc-certbot)

Function Compute to update SSL certificates from [Let's Encrypt](https://letsencrypt.org/es/).

This function uses the [Alibaba Cloud DNS](https://www.alibabacloud.com/product/dns) 
service to authenticate the domain with Let's Encrypt. Your account must have access
to this service, and you must use these enviroment variables to pass the credentials:

* *AUTH_ACCESSKEY_ID*
* *AUTH_ACCESSKEY_SECRET*

The function is intended to be run using a Time trigger. The domain must be passed in the Trigger Message.

## Notes

* The *config.py* file is not provided, as you may already have your own configuration file/system (perhaps even using the enviroment variables of the FC). Just replace the config.config dictionary members with your own cofiguration parameters.
* A sample *Dockerfile* in provided, which you might adjust to your use case.
* A sample *requirements.txt* file is provided, which you might adjust to your use case.
* The FC checks the expiration time of the certificate, to verify if it must be processed.
* The *--test-cert* flag is passed to certbot. This is done mainly for testing, and should be removed for production.

## License

Copyright (c) 2021, Rodolfo González González.

Read the LICENSE file.
