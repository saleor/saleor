'''
Created on Jul 1, 2015

@author: egodolja

'''
'''
import unittest

from mock import MagicMock
from authorizenet import apicontractsv1
#from controller.ARBCancelSubscriptionController import ARBCancelSubscriptionController
from tests import apitestbase
from authorizenet.apicontrollers import *
import test
'''
'''
class ARBCancelSubscriptionControllerTest(apitestbase.ApiTestBase):

    def test_ARBCancelSubscriptionController(self):
        cancelSubscriptionRequest = apicontractsv1.ARBCancelSubscriptionRequest()
        cancelSubscriptionRequest.merchantAuthentication = self.merchantAuthentication
        cancelSubscriptionRequest.refId = 'Sample'
        cancelSubscriptionRequest.subscriptionId = '2680891'
        
        ctrl = ARBCancelSubscriptionController()

        ctrl.execute = MagicMock(return_value=None)

        ctrl.execute(cancelSubscriptionRequest, apicontractsv1.ARBCancelSubscriptionResponse)
        
        ctrl.execute.assert_called_with(cancelSubscriptionRequest, apicontractsv1.ARBCancelSubscriptionResponse)
        ctrl.execute.assert_any_call(cancelSubscriptionRequest, apicontractsv1.ARBCancelSubscriptionResponse)

'''
'''       
class ARBCreateSubscriptionTest(apitestbase.ApiTestBase):

    def testCreateSubscriptionController(self):
        createSubscriptionRequest = apicontractsv1.ARBCreateSubscriptionRequest()
        createSubscriptionRequest.merchantAuthentication = self.merchantAuthentication
        createSubscriptionRequest.refId = 'Sample'
        createSubscriptionRequest.subscription = self.subscriptionOne
    
        ctrl = ARBCreateSubscriptionController()
        
        ctrl.execute = MagicMock(return_value=None)
        
        createRequest = ctrl.ARBCreateSubscriptionController(createSubscriptionRequest)
        ctrl.execute(createRequest, apicontractsv1.ARBCreateSubscriptionResponse)
        
        ctrl.execute.assert_called_with(createRequest, apicontractsv1.ARBCreateSubscriptionResponse )
        ctrl.execute.assert_any_call(createRequest, apicontractsv1.ARBCreateSubscriptionResponse)

class ARBGetSubscriptionStatusTest(object):
    
    
    def testGetSubscriptionStatusController(self):
        getSubscriptionStatusRequest = apicontractsv1.ARBGetSubscriptionStatusRequest()
        getSubscriptionStatusRequest.merchantAuthentication = self.merchantAuthentication
        getSubscriptionStatusRequest.refId = 'Sample'
        getSubscriptionStatusRequest.subscriptionId = '2680891'
    
        ctrl = ARBGetSubscriptionStatusController()
        
        ctrl.execute = MagicMock(return_value=None)
        
        statusRequest = ctrl.ARBGetSubscriptionStatusController(getSubscriptionStatusRequest)
        ctrl.execute(statusRequest, apicontractsv1.ARBGetSubscriptionStatusResponse)
        
        ctrl.execute.assert_called_with(statusRequest, apicontractsv1.ARBGetSubscriptionStatusResponse)
        ctrl.execute.assert_any_call(statusRequest, apicontractsv1.ARBGetSubscriptionStatusResponse)     
'''
    
 
