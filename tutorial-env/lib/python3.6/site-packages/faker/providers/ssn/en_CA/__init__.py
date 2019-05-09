# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as SsnProvider


def checksum(sin):
    """
    Determine validity of a Canadian Social Insurance Number.
    Validation is performed using a modified Luhn Algorithm.  To check
    the Every second digit of the SIN is doubled and the result is
    summed.  If the result is a multiple of ten, the Social Insurance
    Number is considered valid.

    https://en.wikipedia.org/wiki/Social_Insurance_Number
    """

    # Remove spaces and create a list of digits.
    checksumCollection = list(sin.replace(' ', ''))
    checksumCollection = [int(i) for i in checksumCollection]

    # Discard the last digit, we will be calculating it later.
    checksumCollection[-1] = 0

    # Iterate over the provided SIN and double every second digit.
    # In the case that doubling that digit results in a two-digit
    # number, then add the two digits together and keep that sum.

    for i in range(1, len(checksumCollection), 2):
        result = checksumCollection[i] * 2
        if result < 10:
            checksumCollection[i] = result
        else:
            checksumCollection[i] = result - 10 + 1

    # The appropriate checksum digit is the value that, when summed
    # with the first eight values, results in a value divisible by 10

    check_digit = 10 - (sum(checksumCollection) % 10)
    check_digit = (0 if check_digit == 10 else check_digit)

    return check_digit


class Provider(SsnProvider):

    # In order to create a valid SIN we need to provide a number that
    # passes a simple modified Luhn Algorithm checksum.
    #
    # This function reverses the checksum steps to create a random
    # valid nine-digit Canadian SIN (Social Insurance Number) in the
    # format '### ### ###'.
    def ssn(self):

        # Create an array of 8 elements initialized randomly.
        digits = self.generator.random.sample(range(9), 8)

        # The final step of the validation requires that all of the
        # digits sum to a multiple of 10. First, sum the first 8 and
        # set the 9th to the value that results in a multiple of 10.
        check_digit = 10 - (sum(digits) % 10)
        check_digit = (0 if check_digit == 10 else check_digit)

        digits.append(check_digit)

        # digits is now the digital root of the number we want
        # multiplied by the magic number 121 212 121. The next step is
        # to reverse the multiplication which occurred on every other
        # element.
        for i in range(1, len(digits), 2):
            if digits[i] % 2 == 0:
                digits[i] = (digits[i] // 2)
            else:
                digits[i] = (digits[i] + 9) // 2

        # Build the resulting SIN string.
        sin = ""
        for i in range(0, len(digits)):
            sin += str(digits[i])
            # Add a space to make it conform to Canadian formatting.
            if i in (2, 5):
                sin += " "

        # Finally return our random but valid SIN.
        return sin
