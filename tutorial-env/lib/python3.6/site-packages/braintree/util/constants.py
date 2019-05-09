class Constants(object):
    @staticmethod
    def get_all_constant_values_from_class(klass):
        return [klass.__dict__[item] for item in dir(klass) if not item.startswith("__")]
