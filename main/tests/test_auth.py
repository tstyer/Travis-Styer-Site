from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse


class AuthSheetTests(TestCase):
    def _ajax_post(self, url_name, data):
        return self.client.post(
            reverse(url_name),
            data=data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    @patch("main.views.get_users_sheet")
    def test_auth_register_success_sets_session(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = []  # no existing users
        ws.append_row.return_value = None
        mock_get_sheet.return_value = ws

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "Travis"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(self.client.session.get("user_email"), "test@example.com")
        self.assertEqual(self.client.session.get("user_name"), "Travis")

        ws.append_row.assert_called_once()

    def test_auth_register_missing_fields_400(self):
        res = self._ajax_post("auth_register", {"email": "", "password": ""})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    def test_auth_register_duplicate_email_400(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {
                "Email": "test@example.com",
                "User Name": "Old",
                "Password (Now Hashed)": "x",
            }
        ]
        mock_get_sheet.return_value = ws

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "New"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])
        self.assertIn("already", res.json()["error"].lower())

    @patch("main.views.get_users_sheet")
    def test_auth_register_sheet_read_failure_503(self, mock_get_sheet):
        mock_get_sheet.side_effect = Exception("boom")

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "Travis"},
        )
        self.assertEqual(res.status_code, 503)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    def test_auth_register_sheet_write_failure_503(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = []
        ws.append_row.side_effect = Exception("boom")
        mock_get_sheet.return_value = ws

        res = self._ajax_post(
            "auth_register",
            {"email": "test@example.com", "password": "pass1234", "username": "Travis"},
        )
        self.assertEqual(res.status_code, 503)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    @patch("main.views.check_password")
    def test_auth_login_success_sets_session_ajax(
        self, mock_check_password, mock_get_sheet
    ):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {
                "Email": "test@example.com",
                "User Name": "Travis",
                "Password (Now Hashed)": "HASH",
            }
        ]
        mock_get_sheet.return_value = ws
        mock_check_password.return_value = True

        res = self._ajax_post(
            "auth_login",
            {"email": "test@example.com", "password": "pass1234"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(self.client.session.get("user_email"), "test@example.com")
        self.assertEqual(self.client.session.get("user_name"), "Travis")

    @patch("main.views.get_users_sheet")
    def test_auth_login_sheet_read_failure_503_ajax(self, mock_get_sheet):
        mock_get_sheet.side_effect = Exception("boom")

        res = self._ajax_post(
            "auth_login",
            {"email": "test@example.com", "password": "pass1234"},
        )
        self.assertEqual(res.status_code, 503)
        self.assertFalse(res.json()["success"])

    @patch("main.views.get_users_sheet")
    def test_auth_login_invalid_credentials_401_ajax(self, mock_get_sheet):
        ws = MagicMock()
        ws.get_all_records.return_value = [
            {
                "Email": "test@example.com",
                "User Name": "Travis",
                "Password (Now Hashed)": "HASH",
            }
        ]
        mock_get_sheet.return_value = ws

        # no patch check_password -> it will return Falsey in your view flow
        with patch("main.views.check_password", return_value=False):
            res = self._ajax_post(
                "auth_login",
                {"email": "test@example.com", "password": "wrong"},
            )

        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_auth_login_get_not_allowed_ajax(self):
        res = self.client.get(
            reverse("auth_login"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(res.status_code, 405)
        self.assertFalse(res.json()["success"])
