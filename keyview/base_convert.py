'''
Routines for converting between bases.
'''

import string
from util      import is_number


# Encode/decode a to/from base X, where X is the number of URL-safe
# characters.  Also assumed is that number is > 0. None is returned
# on error.
_URL_SAFE_SET = string.digits + string.ascii_letters + "_-.~"


# Encode. Limit to integers; expensive.
def _10baseN(num,b,numerals=_URL_SAFE_SET):
    return ((num == 0) and  "0" ) or ( _10baseN(num // b, b).lstrip("0") + numerals[num % b])
def encode(num):
    if not is_number(num) or num < 0:
        raise Exception("num is not numeric or < 0!")
    return _10baseN(num, len(_URL_SAFE_SET), _URL_SAFE_SET)


# Decode from base > 10, as rep by a string.
def _Nbase10(num_str, numerals=_URL_SAFE_SET):
    if len(num_str) == 0: return 0
    return numerals.index(num_str[-1]) + (len(numerals) * _Nbase10(num_str[:-1]))
def decode(num_str):
    if type(num_str) is not str:
        raise Exception("Requires string input!")
    return _Nbase10(num_str, _URL_SAFE_SET)

