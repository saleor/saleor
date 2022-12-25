'''
Created on Jun 8, 2015

@author: egodolja
'''
import logging

class constants(object):
    """All the constants are defined here
    Define all your constants instead of using magic numbers in the
    code. 
    """
    
    '''Environments'''
    SANDBOX = 'https://apitest.authorize.net/xml/v1/request.api'
    PRODUCTION = 'https://api2.authorize.net/xml/v1/request.api'

    '''clientId'''
    version = '1.1.4'
    clientId = 'sdk-python-' + version

    '''xml encoding'''
    xml_encoding = 'utf-8'
    
    '''xml headers'''
    headers = {'Content-Type' : 'application/xml', 'version' : '1.0', 'encoding' : xml_encoding}
    
    """
    Following constants are defined and used in the ARBSubscriptionStatusController
    Used to remove the "Status" element, that has been deprecated
    However, since the server response still contains it, we have to remove it
    before de-serialization
    """
    '''ARBGetSubscriptionStatus <Status> tag'''
    StatusStart = '<Status>'
    StatusEnd = '</Status>'
    
    '''response encoding'''
    response_encoding = 'ISO-8859-1'
    
    '''note section of subscription status response'''
    note = ' note="Status with a capital \'S\' is obsolete."'
    
    '''ns namespace 1'''
    nsNamespace1 = b'ns1:'
    
    '''ns namespace 2'''
    nsNamespace2 = b':ns1'
    
    '''default log file name'''
    defaultLogFileName = "anetsdk.log"
    
    '''default logging level'''
    defaultLoggingLevel = logging.WARNING
    # defaultLoggingLevel = logging.DEBUG
    
    '''default log format'''
    defaultlogformat = '%(asctime)s %(message)s'
    
    propertiesloggingfilename = "loggingfilename"
    
    propertiesexecutionlogginglevel = "executionlogginglevel"

    defaultLoggerName = "authorizenet.sdk"
    
'''eof'''
