# coding=utf-8

from __future__ import unicode_literals
import hashlib
import string
import uuid
import sys

from .. import BaseProvider


class Provider(BaseProvider):
    def boolean(self, chance_of_getting_true=50):
        return self.generator.random.randint(1, 100) <= chance_of_getting_true

    def null_boolean(self):
        return {
            0: None,
            1: True,
            -1: False,
        }[self.generator.random.randint(-1, 1)]

    def binary(self, length=(1 * 1024 * 1024)):
        """ Returns random binary blob.

        Default blob size is 1 Mb.
        """
        blob = [self.generator.random.randrange(256) for _ in range(length)]
        return bytes(blob) if sys.version_info[0] >= 3 else bytearray(blob)

    def md5(self, raw_output=False):
        """
        Calculates the md5 hash of a given string
        :example 'cfcd208495d565ef66e7dff9f98764da'
        """
        res = hashlib.md5(str(self.generator.random.random()).encode('utf-8'))
        if raw_output:
            return res.digest()
        return res.hexdigest()

    def sha1(self, raw_output=False):
        """
        Calculates the sha1 hash of a given string
        :example 'b5d86317c2a144cd04d0d7c03b2b02666fafadf2'
        """
        res = hashlib.sha1(str(self.generator.random.random()).encode('utf-8'))
        if raw_output:
            return res.digest()
        return res.hexdigest()

    def sha256(self, raw_output=False):
        """
        Calculates the sha256 hash of a given string
        :example '85086017559ccc40638fcde2fecaf295e0de7ca51b7517b6aebeaaf75b4d4654'
        """
        res = hashlib.sha256(
            str(self.generator.random.random()).encode('utf-8'))
        if raw_output:
            return res.digest()
        return res.hexdigest()

    def uuid4(self, cast_to=str):
        """
        Generates a random UUID4 string.
        :param cast_to: Specify what type the UUID should be cast to. Default is `str`
        :type cast_to: callable
        """
        # Based on http://stackoverflow.com/q/41186818
        return cast_to(uuid.UUID(int=self.generator.random.getrandbits(128), version=4))

    def password(
            self,
            length=10,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True):
        """
        Generates a random password.
        @param length: Integer. Length of a password
        @param special_chars: Boolean. Whether to use special characters !@#$%^&*()_+
        @param digits: Boolean. Whether to use digits
        @param upper_case: Boolean. Whether to use upper letters
        @param lower_case: Boolean. Whether to use lower letters
        @return: String. Random password
        """
        choices = ""
        required_tokens = []
        if special_chars:
            required_tokens.append(
                self.generator.random.choice("!@#$%^&*()_+"))
            choices += "!@#$%^&*()_+"
        if digits:
            required_tokens.append(self.generator.random.choice(string.digits))
            choices += string.digits
        if upper_case:
            required_tokens.append(
                self.generator.random.choice(string.ascii_uppercase))
            choices += string.ascii_uppercase
        if lower_case:
            required_tokens.append(
                self.generator.random.choice(string.ascii_lowercase))
            choices += string.ascii_lowercase

        assert len(
            required_tokens) <= length, "Required length is shorter than required characters"

        # Generate a first version of the password
        chars = self.random_choices(choices, length=length)

        # Pick some unique locations
        random_indexes = set()
        while len(random_indexes) < len(required_tokens):
            random_indexes.add(
                self.generator.random.randint(0, len(chars) - 1))

        # Replace them with the required characters
        for i, index in enumerate(random_indexes):
            chars[index] = required_tokens[i]

        return ''.join(chars)
