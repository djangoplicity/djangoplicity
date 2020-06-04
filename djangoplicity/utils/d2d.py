from collections import OrderedDict
from datetime import datetime


class D2dDict(OrderedDict):
    '''
    Remove all initial key/values pairs from d if the value is None
    '''

    def __init__(self, data=None):

        def is_none(val):
            '''
            Return true if val is None or an iterable of None
            '''
            try:
                # Return True if val is an iterable of None
                return all([d is None for d in val])
            except TypeError:
                return val is None

        if data:
            super(D2dDict, self).__init__(
                (k, v) for k, v in data if not is_none(v)
            )
        else:
            super(D2dDict, self).__init__()


def string_to_date(date_string):
    '''
    Convert the given string to a datetime or None if invalid
    Expected format e.g.: 20161128123000
    '''
    if not date_string:
        return None

    try:
        return datetime.strptime(date_string, '%Y%m%d%H%M%S')
    except ValueError:
        # Unrecognized format
        return None
