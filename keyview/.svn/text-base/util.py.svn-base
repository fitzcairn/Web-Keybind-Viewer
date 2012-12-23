'''
Collection of utility methods.
'''


# Determine if a string is a number or not.
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# Render a float to a string with rounding to 3 significant digits.
# Python 2.5 does this weirdly with backticks.
def float_to_str(f):
    return "%0.2f" % f
