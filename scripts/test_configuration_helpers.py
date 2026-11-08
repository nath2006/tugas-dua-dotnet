"""Standard-library regression tests; only synthetic passwords are used."""
import base64
import contextlib
import hashlib
import io
import unittest
from unittest.mock import patch

import configure_local


class ReadPasswordTests(unittest.TestCase):
    def read_with_inputs(self, inputs):
        with patch.object(configure_local.getpass, 'getpass', side_effect=inputs) as hidden_input:
            with contextlib.redirect_stdout(io.StringIO()):
                result = configure_local.read_password('test')
        return result, hidden_input.call_count

    def test_rejects_whitespace_only_then_accepts_valid_password(self):
        valid = 'synthetic-valid-password'
        result, calls = self.read_with_inputs([' ' * 12, ' ' * 12, valid, valid])
        self.assertTrue(result == valid, 'Whitespace-only password was accepted')
        self.assertEqual(calls, 4)

    def test_rejects_over_1024_characters_then_accepts_valid_password(self):
        valid = 'synthetic-valid-password'
        result, calls = self.read_with_inputs(['x' * 1025, 'x' * 1025, valid, valid])
        self.assertTrue(result == valid, 'Overlong password was accepted')
        self.assertEqual(calls, 4)

    def test_preserves_whitespace_in_otherwise_valid_password(self):
        valid = '  synthetic-password  '
        result, calls = self.read_with_inputs([valid, valid])
        self.assertTrue(result == valid, 'Password whitespace was changed')
        self.assertEqual(calls, 2)

    def test_rejects_short_password_then_accepts_12_characters(self):
        valid = 'x' * 12
        result, calls = self.read_with_inputs(['x' * 11, 'x' * 11, valid, valid])
        self.assertTrue(result == valid)
        self.assertEqual(calls, 4)

    def test_rejects_mismatched_confirmation(self):
        valid = 'synthetic-valid-password'
        result, calls = self.read_with_inputs([valid, valid + 'x', valid, valid])
        self.assertTrue(result == valid)
        self.assertEqual(calls, 4)

    def test_accepts_1024_characters(self):
        valid = 'x' * 1024
        result, calls = self.read_with_inputs([valid, valid])
        self.assertTrue(result == valid)
        self.assertEqual(calls, 2)

    def test_accepts_512_emoji_unchanged(self):
        valid = '\U0001f600' * 512
        result, calls = self.read_with_inputs([valid, valid])
        self.assertEqual(result, valid)
        self.assertEqual(calls, 2)

    def test_rejects_513_emoji_then_accepts_valid_password(self):
        invalid = '\U0001f600' * 513
        valid = 'synthetic-valid-password'
        result, calls = self.read_with_inputs([invalid, invalid, valid, valid])
        self.assertEqual(result, valid)
        self.assertEqual(calls, 4)

    def test_mixed_bmp_non_bmp_upper_boundary(self):
        valid = 'x' * 2 + '\U0001f600' * 511
        invalid = valid + 'x'
        result, calls = self.read_with_inputs([invalid, invalid, valid, valid])
        self.assertEqual(result, valid)
        self.assertEqual(calls, 4)


class PasswordHashTests(unittest.TestCase):
    def test_hash_roundtrip_preserves_password_whitespace(self):
        password = '  synthetic-password  '
        iterations, salt, digest = configure_local.password_hash(password).split('.')
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                     base64.b64decode(salt), int(iterations), dklen=32)
        self.assertTrue(actual == base64.b64decode(digest), 'Hash roundtrip failed')
        self.assertEqual(int(iterations), 210000)
        self.assertEqual(len(base64.b64decode(salt)), 16)

    def test_hash_uses_random_salts(self):
        first = configure_local.password_hash('synthetic-password').split('.')
        second = configure_local.password_hash('synthetic-password').split('.')
        self.assertTrue(first[1] != second[1], 'Salts were reused')
        self.assertTrue(first[2] != second[2], 'Salted hashes were identical')


if __name__ == '__main__':
    unittest.main()
