import os
from unittest.mock import patch

import httpx


# Import inside tests to ensure environment is mocked
class TestTrackingTools:

    def test_headers_with_api_key(self) -> None:
        """Test header generation with API key"""
        from sentinel_mas.tools.tracking_tools import _headers

        headers = _headers()
        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Content-Type"] == "application/json"

    def test_headers_without_api_key(self, isolated_environment) -> None:
        """Test header generation without API key"""
        # Set environment without API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True):
            # Re-import config first (it validates OPENAI_API_KEY)
            import importlib

            import sentinel_mas.config

            importlib.reload(sentinel_mas.config)

            # Now import tracking_tools which will use the reloaded config
            from sentinel_mas.tools.tracking_tools import _headers

            headers = _headers()

            assert "Authorization" not in headers
            assert headers["Content-Type"] == "application/json"

    def test_send_track_success(self, mock_http_client) -> None:
        """Test successful track request"""
        # Import inside test to ensure environment is mocked
        from sentinel_mas.tools.tracking_tools import send_track

        mock_client, mock_response = mock_http_client
        mock_response.status_code = 200
        mock_response.json.return_value = {"tracking": True}

        result = send_track.invoke({"resolved_id": "person_123"})

        # Verify the request was made with correct parameters
        mock_client.return_value.__enter__.return_value.request.assert_called_once()
        call_args = mock_client.return_value.__enter__.return_value.request.call_args

        assert call_args[0][0] == "POST"  # method
        # Should use the test URL from mocked environment
        assert call_args[0][1] == "http://test-central:8000/person/track"  # URL
        assert call_args[1]["json"] == {"resolved_id": "person_123"}  # JSON data

        assert result["ok"] is True
        assert result["status_code"] == 200
        assert result["data"]["tracking"] is True

    def test_send_track_missing_resolved_id(self) -> None:
        """Test track request with missing resolved_id"""
        from sentinel_mas.tools.tracking_tools import send_track

        result = send_track.invoke({"resolved_id": ""})

        assert result["ok"] is False
        assert result["status_code"] == 400
        assert "resolved_id is required" in result["error"]

    def test_send_track_http_error(self, mock_http_client) -> None:
        """Test track request with HTTP error"""
        from sentinel_mas.tools.tracking_tools import send_track

        mock_client, mock_response = mock_http_client
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Person not found"}
        mock_response.text = '{"detail": "Person not found"}'

        result = send_track.invoke({"resolved_id": "nonexistent"})

        assert result["ok"] is False
        assert result["status_code"] == 404
        assert "Person not found" in result["error"]

    def test_send_cancel_success(self, mock_http_client) -> None:
        """Test successful cancel tracking request"""
        from sentinel_mas.tools.tracking_tools import send_cancel

        mock_client, mock_response = mock_http_client
        mock_response.status_code = 200
        mock_response.json.return_value = {"tracking": False}

        result = send_cancel.invoke({"resolved_id": "person_123"})

        # Verify the request was made with correct parameters
        mock_client.return_value.__enter__.return_value.request.assert_called_once()
        call_args = mock_client.return_value.__enter__.return_value.request.call_args

        assert call_args[0][0] == "POST"  # method
        assert call_args[0][1] == "http://test-central:8000/person/untrack"  # URL
        assert call_args[1]["json"] == {"resolved_id": "person_123"}  # JSON data

        assert result["ok"] is True
        assert result["status_code"] == 200
        assert result["data"]["tracking"] is False

    def test_send_cancel_missing_resolved_id(self) -> None:
        """Test cancel request with missing resolved_id"""
        from sentinel_mas.tools.tracking_tools import send_cancel

        result = send_cancel.invoke({"resolved_id": ""})

        assert result["ok"] is False
        assert result["status_code"] == 400
        assert "resolved_id is required" in result["error"]

    def test_get_track_status_success(self, mock_http_client) -> None:
        """Test successful track status request"""
        from sentinel_mas.tools.tracking_tools import get_track_status

        mock_client, mock_response = mock_http_client
        mock_response.status_code = 200
        mock_response.json.return_value = {"is_tracked": True}

        result = get_track_status.invoke({"resolved_id": "person_123"})

        # Verify the request was made with correct parameters
        mock_client.return_value.__enter__.return_value.request.assert_called_once()
        call_args = mock_client.return_value.__enter__.return_value.request.call_args

        assert call_args[0][0] == "GET"  # method
        assert (
            call_args[0][1] == "http://test-central:8000/person/person_123/tracking"
        )  # URL

        assert result["ok"] is True
        assert result["data"]["is_tracked"] is True

    def test_get_track_status_missing_resolved_id(self) -> None:
        """Test track status request with missing resolved_id"""
        from sentinel_mas.tools.tracking_tools import get_track_status

        result = get_track_status.invoke({"resolved_id": ""})

        assert result["ok"] is False
        assert result["status_code"] == 400
        assert "resolved_id is required" in result["error"]

    def test_get_person_insight_success(self, mock_http_client) -> None:
        """Test successful person insight request"""
        from sentinel_mas.tools.tracking_tools import get_person_insight

        mock_client, mock_response = mock_http_client
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "last_movement": {"location": "Zone A", "timestamp": 1609459200000},
            "last_event": {"incident": "intrusion", "confidence": 0.95},
        }

        result = get_person_insight.invoke({"resolved_id": "person_123"})

        # Verify the request was made with correct parameters
        mock_client.return_value.__enter__.return_value.request.assert_called_once()
        call_args = mock_client.return_value.__enter__.return_value.request.call_args

        assert call_args[0][0] == "GET"  # method
        assert call_args[0][1] == "http://test-central:8000/insight/person_123"  # URL

        assert result["ok"] is True
        assert "last_movement" in result["data"]
        assert "last_event" in result["data"]

    def test_get_person_insight_missing_resolved_id(self) -> None:
        """Test person insight request with missing resolved_id"""
        from sentinel_mas.tools.tracking_tools import get_person_insight

        result = get_person_insight.invoke({"resolved_id": ""})

        assert result["ok"] is False
        assert result["status_code"] == 400
        assert "resolved_id is required" in result["error"]

    def test_connection_error_retry(self, mock_http_client) -> None:
        """Test retry behavior on connection errors"""
        from sentinel_mas.tools.tracking_tools import send_track

        mock_client, mock_response = mock_http_client

        # Mock the client to raise connection error first, then succeed
        mock_request = mock_client.return_value.__enter__.return_value.request
        mock_request.side_effect = [
            httpx.ConnectError("Connection failed"),
            mock_response,  # Succeed on retry
        ]

        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        result = send_track.invoke({"resolved_id": "person_123"})

        # Should succeed after retry
        assert result["ok"] is True
        # Should have been called twice (initial + retry)
        assert mock_request.call_count == 2

    def test_all_retries_fail(self, mock_http_client) -> None:
        """Test behavior when all retries fail"""
        from sentinel_mas.tools.tracking_tools import send_track

        mock_client, mock_response = mock_http_client

        # Mock the client to always raise connection errors
        mock_request = mock_client.return_value.__enter__.return_value.request
        mock_request.side_effect = httpx.ConnectError("Connection failed")

        result = send_track.invoke({"resolved_id": "person_123"})

        # Should fail after all retries
        assert result["ok"] is False
        assert result["status_code"] == 599
        assert "ConnectError" in result["error"]
        # Should have been called MAX_RETRIES + 1 times
        assert mock_request.call_count == 3  # (MAX_RETRIES=2 + initial attempt)
