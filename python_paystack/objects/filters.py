class Filter():
    '''
    Filter class for checking through dicts
    '''

    @staticmethod
    def find_key_value(key, dataset):
        '''
        Function for getting the value of a the key passed in (provided it exists)
        Returns True and the value if the key is found or False and 0 when it isn't

        Arguments:
        key : dictionary key to be searched for
        '''

        dicts = []

        if not isinstance(dataset, dict):
            raise TypeError("dataset argument should be a dictionary")

        for item in dataset:

            if isinstance(dataset[item], dict):
                dicts.append(dataset[item])
                continue
            if item == key:
                return (True, dataset[item])

        for dataset in dicts:
            return Filter.find_key_value(key, dataset)

        return (False, 0)


    @staticmethod
    def filter_amount(amount_range: range, dataset, amount_key='amount'):
        '''
        Checks if there is an amount in the amount_range given in the dataset
        '''
        if not isinstance(dataset, dict):
            raise TypeError("dataset argument should be a dictionary")

        if not isinstance(amount_range, range):
            raise TypeError("amount_range should be of type 'range' ")

        status, value = Filter.find_key_value(amount_key, dataset)

        if status:
            if value in amount_range:
                return True
        else:
            raise AttributeError("'amount_key' key not found in dataset")

        return False
