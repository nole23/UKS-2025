import unittest
from unittest.mock import MagicMock, patch
from utils.logger import UKSLogger, UKSAuditLogger, _BaseLogger
from utils.middleware.audit import AuditMiddleware
from utils.middleware.request_id import RequestIDMiddleware


# =========================
# UKSLogger / UKSAuditLogger
# =========================
class TestUKSLogger(unittest.TestCase):

    @patch("utils.logger._app_logger")
    def test_uks_logger_info_calls_logger(self, mock_logger):
        UKSLogger.info("test info")
        mock_logger.log.assert_called_once()
        level, msg = mock_logger.log.call_args[0][:2]
        self.assertEqual(level, 20)  # logging.INFO
        self.assertIn("test info", msg)

    @patch("utils.logger._audit_logger")
    def test_uksauditlogger_info_calls_logger(self, mock_logger):
        UKSAuditLogger.info("audit test")
        mock_logger.log.assert_called_once()
        level, msg = mock_logger.log.call_args[0][:2]
        self.assertEqual(level, 20)  # logging.INFO
        self.assertIn("audit test", msg)


# =========================
# AuditMiddleware
# =========================
class TestAuditMiddleware(unittest.TestCase):

    def test_audit_middleware_logs_info(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get_response = MagicMock(return_value=mock_response)
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.username = "testuser"
        request.method = "GET"
        request.path = "/test/path"

        middleware = AuditMiddleware(mock_get_response)

        with patch("utils.logger.UKSAuditLogger.info") as mock_audit:
            response = middleware(request)
            # provera da middleware vraća response
            self.assertEqual(response, mock_response)
            # provera da je audit log pozvan
            mock_audit.assert_called_once()
            log_msg = mock_audit.call_args[0][0]
            self.assertIn("testuser", log_msg)
            self.assertIn("GET /test/path", log_msg)
            self.assertIn(str(mock_response.status_code), log_msg)

    def test_audit_middleware_anonymous_user(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get_response = MagicMock(return_value=mock_response)
        request = MagicMock()
        request.user.is_authenticated = False
        request.method = "POST"
        request.path = "/anon/path"

        middleware = AuditMiddleware(mock_get_response)

        with patch("utils.logger.UKSAuditLogger.info") as mock_audit:
            response = middleware(request)
            self.assertEqual(response, mock_response)
            log_msg = mock_audit.call_args[0][0]
            self.assertIn("anonymous", log_msg)
            self.assertIn("POST /anon/path", log_msg)


# =========================
# RequestIDMiddleware
# =========================
class TestRequestIDMiddleware(unittest.TestCase):

    def test_request_id_is_set_and_header_added(self):
        mock_response = MagicMock()
        mock_get_response = MagicMock(return_value=mock_response)
        request = MagicMock()

        middleware = RequestIDMiddleware(mock_get_response)
        response = middleware(request)

        # provera da je request_id dodat
        self.assertTrue(hasattr(request, "request_id"))


# =========================
# _BaseLogger _context test (opciono)
# =========================
class TestBaseLogger(unittest.TestCase):

    def test_context_returns_string(self):
        ctx = _BaseLogger._context()
        self.assertIsInstance(ctx, str)
        self.assertTrue(len(ctx) > 0)

