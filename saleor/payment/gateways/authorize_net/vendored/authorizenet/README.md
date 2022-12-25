# Authorize.Net Python SDK 

[![Travis CI Status](https://travis-ci.org/AuthorizeNet/sdk-python.svg?branch=master)](https://travis-ci.org/AuthorizeNet/sdk-python)
[![Coverage Status](https://coveralls.io/repos/github/AuthorizeNet/sdk-python/badge.svg?branch=master)](https://coveralls.io/github/AuthorizeNet/sdk-python?branch=master)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/AuthorizeNet/sdk-python/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/AuthorizeNet/sdk-python/?branch=master)
[![PyPI](https://img.shields.io/pypi/v/authorizenet.svg)](https://badge.fury.io/py/authorizenet)


## Requirements
* For Python 2, Python 2.7 or greater
* For Python 3, Python 3.4 or later
* OpenSSL 1.0.2 or greater
* An Authorize.Net account (see _Registration & Configuration_ section below)

_Note: Our goal is ensuring this SDK is compatible with Python 2.7+, 3.4+ and PyPy, but at the moment we're primarily testing against Python 2.7._

### Contribution  
  - If you need information or clarification about Authorize.Net features, create an issue with your question. You can also search the [Authorize.Net developer community](https://community.developer.authorize.net/) for discussions related to your question.
  - Before creating pull requests, please read [the contributors guide](CONTRIBUTING.md).

### TLS 1.2
The Authorize.Net APIs only support connections using the TLS 1.2 security protocol. Make sure to upgrade all required components to support TLS 1.2. Keep these components up to date to mitigate the risk of new security flaws.


## Installation
To install the AuthorizeNet Python SDK:

`pip install authorizenet`


## Registration & Configuration
Use of this SDK and the Authorize.Net APIs requires having an account on the Authorize.Net system. You can find these details in the Settings section.
If you don't currently have a production Authorize.Net account, [sign up for a sandbox account](https://developer.authorize.net/sandbox/).

### Authentication
To authenticate with the Authorize.Net API, use your account's API Login ID and Transaction Key. If you don't have these credentials, obtain them from the Merchant Interface.  For production accounts, the Merchant Interface is located at (https://account.authorize.net/), and for sandbox accounts, at (https://sandbox.authorize.net).

After you have your credentials, load them into the appropriate variables in your code. The below sample code shows how to set the credentials as part of the API request. 

#### To set your API credentials for an API request:
```python
	merchantAuth = apicontractsv1.merchantAuthenticationType()
	merchantAuth.name = 'YOUR_API_LOGIN_ID'
	merchantAuth.transactionKey = 'YOUR_TRANSACTION_KEY'
```

Never include your API Login ID and Transaction Key directly in a file in a publicly accessible portion of your website. As a best practice, define the API Login ID and Transaction Key in a constants file, and reference those constants in your code.

### Switching between the sandbox environment and the production environment
Authorize.Net maintains a complete sandbox environment for testing and development purposes. The sandbox environment is an exact replica of our production environment, with simulated transaction authorization and settlement. By default, this SDK is configured to use the sandbox environment. To switch to the production environment, use the `setenvironment` method on the controller before executing. For example:
```python
# For PRODUCTION use
	createtransactioncontroller.setenvironment(constants.PRODUCTION)
```

API credentials are different for each environment, so be sure to switch to the appropriate credentials when switching environments.

### Enable Logging in the SDK
Python SDK uses the logger _'authorizenet.sdk'_. By default, the logger in the SDK is not configured to write output. You can configure the logger in your code to start seeing logs from the SDK.

A sample logger configuration is given as below:

```python
	import logging
	logger = logging.getLogger('authorizenet.sdk')
	handler = logging.FileHandler('anetSdk.log')  
	formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)
	logger.debug('Logger set up for Authorizenet Python SDK complete')
``` 


## SDK Usage Examples and Sample Code
When using this SDK, downloading the Authorize.Net sample code repository is recommended.
* [Authorize.Net Python Sample Code Repository (on GitHub)](https://github.com/AuthorizeNet/sample-code-python)

The repository contains comprehensive sample code for common uses of the Authorize.Net API.

The API Reference contains details and examples of the structure and formatting of the Authorize.Net API.
* [Developer Center API Reference](http://developer.authorize.net/api/reference/index.html)

Use the examples in the API Reference to determine which methods and information to include in an API request using this SDK.

## Create a Chase Pay Transaction

Use this method to authorize and capture a payment using a tokenized credit card number issued by Chase Pay. Chase Pay transactions are only available to merchants using the Paymentech processor.

The following information is required in the request:
- The **payment token**,
- The **expiration date**,
- The **cryptogram** received from the token provider,
- The **tokenRequestorName**,
- The **tokenRequestorId**, and
- The **tokenRequestorEci**.

When using the SDK to submit Chase Pay transactions, consider the following points:
- `tokenRequesterName` must be populated with **`”CHASE_PAY”`**
- `tokenRequestorId` must be populated with the **`Token Requestor ID`** provided by Chase Pay services for each transaction during consumer checkout
- `tokenRequesterEci` must be populated with the **`ECI Indicator`** provided by Chase Pay services for each transaction during consumer checkout 

## Building & Testing the SDK

### Requirements
- python 2.7
- pyxb 1.2.5

Run the following to get pyxb and nosetests:
- pip install pyxb==1.2.5
- pip install nose
- pip install lxml

### Running the SDK Tests
- Tests available are: unit tests, mock tests, sample code
- use nosetests to run all unittests

`>nosetests`

### Testing Guide
For additional help in testing your own code, Authorize.Net maintains a [comprehensive testing guide](http://developer.authorize.net/hello_world/testing_guide/) that includes test credit card numbers to use and special triggers to generate certain responses from the sandbox environment.

### Transaction Hash Upgrade
Authorize.Net is phasing out the MD5 based `transHash` element in favor of the SHA-512 based `transHashSHA2`. The setting in the Merchant Interface which controlled the MD5 Hash option is no longer available, and the `transHash` element will stop returning values at a later date to be determined. For information on how to use `transHashSHA2`, see the [Transaction Hash Upgrade Guide] (https://developer.authorize.net/support/hash_upgrade/).

## License
This repository is distributed under a proprietary license. See the provided [`LICENSE.txt`](/LICENSE.txt) file.
