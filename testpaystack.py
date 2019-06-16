from python_paystack.paystack_config import PaystackConfig

PaystackConfig.SECRET_KEY  = 'sk_test_49261090f25a598b130ba6284752d8fca421b92c'
PaystackConfig.PUBLIC_KEY = 'pk_test_48015e5bc54bf6b5ff0f3e7e1a3c8e1ab9cc4a4d'

from python_paystack.objects.transactions import Transaction
from python_paystack.managers import TransactionsManager

transaction = Transaction(20, 'email@test.com')
transaction_manager = TransactionsManager()
print(transaction_manager.verify_transaction('eip7zkgvih'))
# transaction = transaction_manager.initialize_transaction('STANDARD', transaction)
#Starts a standard transaction and returns a transaction object

# print('==========>', transaction.authorization_url)
#Gives the authorization_url for the transaction

#Transactions can easily be verified like so
# transaction = transaction_manager.verify_transaction(transaction)