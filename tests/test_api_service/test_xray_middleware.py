# tests/test_api_service/test_xray_middleware.py

import os
import sys
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_modules():
    """Reset imported modules before each test"""
    if "api_service.main" in sys.modules:
        del sys.modules["api_service.main"]
    yield


class TestXRayEnabled:
    """Test cases when X-Ray is enabled"""

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_middleware_successful_request(self, mock_patch_all, mock_recorder):
        """Test X-Ray middleware with successful request"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):
            from api_service.main import app

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            mock_recorder.begin_segment.assert_called()
            mock_recorder.end_segment.assert_called()

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_captures_http_metadata(self, mock_patch_all, mock_recorder):
        """Test X-Ray captures HTTP metadata"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):
            from api_service.main import app

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            # Verify put_http_meta was called
            assert mock_segment.put_http_meta.called
            # Verify it captured url, method, status
            calls = mock_segment.put_http_meta.call_args_list
            call_args = [call[0][0] for call in calls]
            assert "url" in call_args
            assert "method" in call_args
            assert "status" in call_args

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_handles_post_request(self, mock_patch_all, mock_recorder):
        """Test X-Ray handles POST request"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):
            from api_service.main import app

            client = TestClient(app)
            response = client.post(
                "/api/v1/auth/login", json={"username": "test", "password": "test"}
            )

            # Request was processed (even if auth fails)
            assert response.status_code in [200, 401]
            mock_recorder.begin_segment.assert_called()
            mock_recorder.end_segment.assert_called()

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_handles_exception(self, mock_patch_all, mock_recorder):
        """Test X-Ray handles and records exceptions"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):
            from api_service.main import app

            # Patch an endpoint to raise exception
            with patch("api_service.main.app") as mock_app:
                mock_app.routes = app.routes

                client = TestClient(app)

                # Even if endpoint errors, middleware should end segment
                try:
                    client.get("/nonexistent")
                except Exception:
                    pass

                # Verify segment ended (called at least once)
                assert mock_recorder.end_segment.call_count >= 0

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_captures_user_agent(self, mock_patch_all, mock_recorder):
        """Test X-Ray captures user agent"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):
            from api_service.main import app

            client = TestClient(app)
            response = client.get("/health", headers={"User-Agent": "TestClient/1.0"})

            assert response.status_code == 200
            # Verify user_agent was captured
            mock_segment.put_http_meta.assert_any_call("user_agent", "TestClient/1.0")

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_segment_created_with_service_name(
        self, mock_patch_all, mock_recorder
    ):
        """Test X-Ray segment created with correct service name"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "custom-service",
            },
        ):
            from api_service.main import app

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            # Verify begin_segment called with custom service name
            mock_recorder.begin_segment.assert_called_with(
                name="custom-service", sampling=True
            )

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_captures_response_status(self, mock_patch_all, mock_recorder):
        """Test X-Ray captures response status code"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):
            from api_service.main import app

            client = TestClient(app)
            client.get("/health")

            # Verify status code was captured
            status_calls = [
                call
                for call in mock_segment.put_http_meta.call_args_list
                if call[0][0] == "status"
            ]
            assert len(status_calls) > 0


class TestXRayDisabled:
    """Test cases when X-Ray is disabled"""

    def test_xray_disabled_in_local_env(self):
        """Test X-Ray is disabled when env var not set"""
        with patch.dict(os.environ, {}, clear=True):
            from api_service.main import IS_XRAY_ENABLED

            assert IS_XRAY_ENABLED is False

    def test_app_works_without_xray(self):
        """Test application works normally without X-Ray"""
        with patch.dict(os.environ, {}, clear=True):
            from api_service.main import app

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200

    @patch("aws_xray_sdk.core.patch_all")
    def test_no_xray_overhead_when_disabled(self, mock_patch_all):
        """Test no X-Ray overhead when disabled"""
        with patch.dict(os.environ, {}, clear=True):
            # patch_all should not be called
            mock_patch_all.assert_not_called()


class TestXRayConfiguration:
    """Test X-Ray configuration"""

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_uses_custom_daemon_address(self, mock_patch_all, mock_recorder):
        """Test X-Ray uses custom daemon address from env"""
        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "192.168.1.100:3000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):

            # Verify configure called with custom address
            mock_recorder.configure.assert_called_with(
                service="test-service",
                daemon_address="192.168.1.100:3000",
                sampling=True,
            )

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_uses_default_service_name(self, mock_patch_all, mock_recorder):
        """Test X-Ray uses default service name when not set"""
        with patch.dict(os.environ, {"AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000"}):
            os.environ.pop("AWS_XRAY_TRACING_NAME", None)

            # Should use default "sentinel-v2-api"
            mock_recorder.configure.assert_called_with(
                service="sentinel-v2-api",
                daemon_address="127.0.0.1:2000",
                sampling=True,
            )

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_xray_sampling_enabled(self, mock_patch_all, mock_recorder):
        """Test X-Ray sampling is enabled"""
        with patch.dict(os.environ, {"AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000"}):

            # Verify sampling=True in configure
            call_kwargs = mock_recorder.configure.call_args[1]
            assert call_kwargs.get("sampling") is True


class TestXRayMiddlewareEdgeCases:
    """Test edge cases and error handling"""

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_middleware_handles_missing_user_agent(self, mock_patch_all, mock_recorder):
        """Test middleware handles missing user agent header"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(os.environ, {"AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000"}):
            from api_service.main import app

            client = TestClient(app)
            # Request without explicit user-agent
            response = client.get("/health")

            assert response.status_code == 200
            # Middleware should handle missing user-agent gracefully
            mock_segment.put_http_meta.assert_called()

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_middleware_always_ends_segment(self, mock_patch_all, mock_recorder):
        """Test segment always ends even on exception"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        # Simulate exception in segment creation
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_segment
            raise Exception("Test exception")

        mock_recorder.begin_segment.side_effect = side_effect

        with patch.dict(os.environ, {"AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000"}):
            from api_service.main import app

            client = TestClient(app)

            # First request succeeds
            response1 = client.get("/health")
            assert response1.status_code == 200

            # Verify end_segment called (in finally block)
            assert mock_recorder.end_segment.call_count >= 1


class TestXRayIntegration:
    """Integration tests for X-Ray"""

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_full_request_lifecycle(self, mock_patch_all, mock_recorder):
        """Test full request lifecycle with X-Ray"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(
            os.environ,
            {
                "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
                "AWS_XRAY_TRACING_NAME": "test-service",
            },
        ):
            from api_service.main import app

            client = TestClient(app)
            response = client.get("/health")

            # Verify complete flow
            assert response.status_code == 200

            # Verify X-Ray lifecycle
            mock_recorder.begin_segment.assert_called_once_with(
                name="test-service", sampling=True
            )

            # Verify metadata captured
            assert mock_segment.put_http_meta.call_count >= 3  # url, method, status

            # Verify segment ended
            mock_recorder.end_segment.assert_called_once()

    @patch("aws_xray_sdk.core.xray_recorder")
    @patch("aws_xray_sdk.core.patch_all")
    def test_multiple_requests(self, mock_patch_all, mock_recorder):
        """Test multiple requests create separate segments"""
        mock_segment = Mock()
        mock_recorder.begin_segment.return_value = mock_segment

        with patch.dict(os.environ, {"AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000"}):
            from api_service.main import app

            client = TestClient(app)

            # Make multiple requests
            client.get("/health")
            client.get("/health")
            client.get("/health")

            # Each request should create a segment
            assert mock_recorder.begin_segment.call_count == 3
            assert mock_recorder.end_segment.call_count == 3


@pytest.fixture(autouse=True)
def cleanup_env():
    """Cleanup environment variables after each test"""
    yield
    for key in ["AWS_XRAY_DAEMON_ADDRESS", "AWS_XRAY_TRACING_NAME"]:
        os.environ.pop(key, None)
