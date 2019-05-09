# coding=utf-8

from __future__ import unicode_literals

from .. import Provider as SsnProvider


def checksum(digits):
    """
    Returns the checksum of CPF digits.
    References to the algorithm:
    https://pt.wikipedia.org/wiki/Cadastro_de_pessoas_f%C3%ADsicas#Algoritmo
    https://metacpan.org/source/MAMAWE/Algorithm-CheckDigits-v1.3.0/lib/Algorithm/CheckDigits/M11_004.pm
    """
    s = 0
    p = len(digits) + 1
    for i in range(0, len(digits)):
        s += digits[i] * p
        p -= 1

    reminder = s % 11
    if reminder == 0 or reminder == 1:
        return 0
    else:
        return 11 - reminder


class Provider(SsnProvider):
    """
    Provider for Brazilian SSN also known in Brazil as CPF.
    There are two methods Provider.ssn and Provider.cpf
    The snn returns a valid number with numbers only
    The cpf return a valid number formatted with brazilian mask. eg nnn.nnn.nnn-nn
    """

    def ssn(self):
        digits = self.generator.random.sample(range(10), 9)

        dv = checksum(digits)
        digits.append(dv)
        digits.append(checksum(digits))

        return ''.join(map(str, digits))

    def cpf(self):
        c = self.ssn()
        return c[:3] + '.' + c[3:6] + '.' + c[6:9] + '-' + c[9:]

    def rg(self):
        """
        Brazilian RG, return plain numbers.
        Check:  https://www.ngmatematica.com/2014/02/como-determinar-o-digito-verificador-do.html
        """

        digits = self.generator.random.sample(range(0, 9), 8)
        checksum = sum(i * digits[i - 2] for i in range(2, 10))
        last_digit = 11 - (checksum % 11)

        if last_digit == 10:
            digits.append('X')
        elif last_digit == 11:
            digits.append(0)
        else:
            digits.append(last_digit)

        return ''.join(map(str, digits))
