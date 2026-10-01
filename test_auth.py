"""
Unit tests for auth_manager module.
Verifies bcrypt password hashing, credential validation, and password changing.
"""

import os
import unittest
import auth_manager


class TestAuthManager(unittest.TestCase):
    def setUp(self):
        # Reset auth store for test isolation if needed
        self.username = "vishal"
        self.default_pass = "admin123"

    def test_hash_and_check_password(self):
        pwd = "SecretPassword123!"
        hashed = auth_manager.hash_password(pwd)
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))
        self.assertTrue(auth_manager.check_password(pwd, hashed))
        self.assertFalse(auth_manager.check_password("WrongPassword", hashed))

    def test_authenticate_default_user_success(self):
        ok, msg, user = auth_manager.authenticate_user(self.username, self.default_pass)
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertEqual(user.get("username"), "vishal")
        self.assertNotIn("password_hash", user)

    def test_authenticate_invalid_credentials(self):
        ok, msg, user = auth_manager.authenticate_user(self.username, "invalid_password")
        self.assertFalse(ok)
        self.assertIsNone(user)

        ok2, msg2, user2 = auth_manager.authenticate_user("nonexistent_user", "password")
        self.assertFalse(ok2)
        self.assertIsNone(user2)

    def test_change_password_workflow(self):
        # Change password to new one
        new_pwd = "NewSecurePassword456!"
        ok, msg = auth_manager.change_user_password(self.username, self.default_pass, new_pwd)
        self.assertTrue(ok)

        # Authenticate with new password
        ok_new, _, user_new = auth_manager.authenticate_user(self.username, new_pwd)
        self.assertTrue(ok_new)

        # Authenticate with old password fails
        ok_old, _, _ = auth_manager.authenticate_user(self.username, self.default_pass)
        self.assertFalse(ok_old)

        # Revert back to default_pass
        ok_rev, _ = auth_manager.change_user_password(self.username, new_pwd, self.default_pass)
        self.assertTrue(ok_rev)


if __name__ == "__main__":
    unittest.main()
