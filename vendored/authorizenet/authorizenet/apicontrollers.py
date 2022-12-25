'''
Created on Nov 15, 2017

@author: krgupta
'''
import logging
from authorizenet.constants import constants
from authorizenet import apicontractsv1
from authorizenet import apicontrollersbase   

anetLogger = logging.getLogger(constants.defaultLoggerName)
 
class ARBCancelSubscriptionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(ARBCancelSubscriptionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'ARBCancelSubscriptionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.ARBCancelSubscriptionResponse() 
    
class ARBCreateSubscriptionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(ARBCreateSubscriptionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'ARBCreateSubscriptionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.ARBCreateSubscriptionResponse()
     
class ARBGetSubscriptionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(ARBGetSubscriptionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'ARBGetSubscriptionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.ARBGetSubscriptionResponse() 
class ARBGetSubscriptionListController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(ARBGetSubscriptionListController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'ARBGetSubscriptionListRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.ARBGetSubscriptionListResponse() 
    
class ARBGetSubscriptionStatusController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(ARBGetSubscriptionStatusController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'ARBGetSubscriptionStatusRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.ARBGetSubscriptionStatusResponse()
    
    def afterexecute(self):
        response = self._httpResponse
        if constants.note in response:
            response = response.replace(constants.note, '')

        if constants.StatusStart in response:
            start = response.index(constants.StatusStart)
            end = response.index(constants.StatusEnd)
            response = response.replace(response[start:end+9], '')

        self._httpResponse = response
        return
		
class ARBUpdateSubscriptionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(ARBUpdateSubscriptionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'ARBUpdateSubscriptionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.ARBUpdateSubscriptionResponse() 
class authenticateTestController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(authenticateTestController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'authenticateTestRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.authenticateTestResponse() 
class createCustomerPaymentProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(createCustomerPaymentProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'createCustomerPaymentProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.createCustomerPaymentProfileResponse() 
class createCustomerProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(createCustomerProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'createCustomerProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.createCustomerProfileResponse() 
class createCustomerProfileFromTransactionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(createCustomerProfileFromTransactionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'createCustomerProfileFromTransactionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.createCustomerProfileResponse() 
class createCustomerProfileTransactionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(createCustomerProfileTransactionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'createCustomerProfileTransactionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.createCustomerProfileTransactionResponse() 
class createCustomerShippingAddressController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(createCustomerShippingAddressController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'createCustomerShippingAddressRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.createCustomerShippingAddressResponse() 
class createTransactionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(createTransactionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'createTransactionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.createTransactionResponse() 
class decryptPaymentDataController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(decryptPaymentDataController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'decryptPaymentDataRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.decryptPaymentDataResponse() 
class deleteCustomerPaymentProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(deleteCustomerPaymentProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'deleteCustomerPaymentProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.deleteCustomerPaymentProfileResponse() 
class deleteCustomerProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(deleteCustomerProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'deleteCustomerProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.deleteCustomerProfileResponse() 
class deleteCustomerShippingAddressController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(deleteCustomerShippingAddressController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'deleteCustomerShippingAddressRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.deleteCustomerShippingAddressResponse() 
class ErrorController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(ErrorController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'ErrorRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.ErrorResponse() 
class getAUJobDetailsController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getAUJobDetailsController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getAUJobDetailsRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getAUJobDetailsResponse() 
class getAUJobSummaryController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getAUJobSummaryController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getAUJobSummaryRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getAUJobSummaryResponse() 
class getBatchStatisticsController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getBatchStatisticsController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getBatchStatisticsRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getBatchStatisticsResponse() 
class getCustomerPaymentProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getCustomerPaymentProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getCustomerPaymentProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getCustomerPaymentProfileResponse() 
class getCustomerPaymentProfileListController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getCustomerPaymentProfileListController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getCustomerPaymentProfileListRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getCustomerPaymentProfileListResponse() 
class getCustomerProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getCustomerProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getCustomerProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getCustomerProfileResponse() 
class getCustomerProfileIdsController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getCustomerProfileIdsController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getCustomerProfileIdsRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getCustomerProfileIdsResponse() 
class getCustomerShippingAddressController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getCustomerShippingAddressController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getCustomerShippingAddressRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getCustomerShippingAddressResponse() 
class getHostedPaymentPageController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getHostedPaymentPageController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getHostedPaymentPageRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getHostedPaymentPageResponse() 
class getHostedProfilePageController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getHostedProfilePageController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getHostedProfilePageRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getHostedProfilePageResponse() 
class getMerchantDetailsController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getMerchantDetailsController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getMerchantDetailsRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getMerchantDetailsResponse() 
class getSettledBatchListController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getSettledBatchListController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getSettledBatchListRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getSettledBatchListResponse() 
class getTransactionDetailsController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getTransactionDetailsController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getTransactionDetailsRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getTransactionDetailsResponse() 
class getTransactionListController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getTransactionListController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getTransactionListRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getTransactionListResponse() 
class getTransactionListForCustomerController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getTransactionListForCustomerController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getTransactionListForCustomerRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getTransactionListResponse() 
class getUnsettledTransactionListController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(getUnsettledTransactionListController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'getUnsettledTransactionListRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.getUnsettledTransactionListResponse() 
class isAliveController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(isAliveController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'isAliveRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.isAliveResponse() 
class logoutController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(logoutController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'logoutRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.logoutResponse() 
class mobileDeviceLoginController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(mobileDeviceLoginController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'mobileDeviceLoginRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.mobileDeviceLoginResponse() 
class mobileDeviceRegistrationController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(mobileDeviceRegistrationController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'mobileDeviceRegistrationRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.mobileDeviceRegistrationResponse() 
class securePaymentContainerController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(securePaymentContainerController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'securePaymentContainerRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.securePaymentContainerResponse() 
class sendCustomerTransactionReceiptController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(sendCustomerTransactionReceiptController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'sendCustomerTransactionReceiptRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.sendCustomerTransactionReceiptResponse() 
class updateCustomerPaymentProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(updateCustomerPaymentProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'updateCustomerPaymentProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.updateCustomerPaymentProfileResponse() 
class updateCustomerProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(updateCustomerProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'updateCustomerProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.updateCustomerProfileResponse() 
class updateCustomerShippingAddressController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(updateCustomerShippingAddressController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'updateCustomerShippingAddressRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.updateCustomerShippingAddressResponse() 
class updateHeldTransactionController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(updateHeldTransactionController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'updateHeldTransactionRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.updateHeldTransactionResponse() 
class updateMerchantDetailsController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(updateMerchantDetailsController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'updateMerchantDetailsRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.updateMerchantDetailsResponse() 
class updateSplitTenderGroupController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(updateSplitTenderGroupController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'updateSplitTenderGroupRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.updateSplitTenderGroupResponse() 
class validateCustomerPaymentProfileController(apicontrollersbase.APIOperationBase):
    
    def __init__(self, apirequest):
        super(validateCustomerPaymentProfileController, self).__init__(apirequest)
        return 
    
    def validaterequest(self):
        anetLogger.debug('performing custom validation..') 
        #validate required fields
        #if (self._request.xyz == "null"):
        #    raise ValueError('xyz is required')         
        return
    
    def getrequesttype(self):
        '''Returns request type''' 
        return 'validateCustomerPaymentProfileRequest'

    def getresponseclass(self):
        ''' Returns the response class '''
        return apicontractsv1.validateCustomerPaymentProfileResponse()
