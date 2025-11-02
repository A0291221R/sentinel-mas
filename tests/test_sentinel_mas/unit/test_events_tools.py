from typing import Any

from sentinel_mas.tools.events_tools import (
    _clamp_limit,
    list_anomaly_event,
    who_entered_zone,
)


class TestEventsTools:

    def test_clamp_limit(self) -> None:
        """Test limit clamping utility"""
        assert _clamp_limit(None) == 50
        assert _clamp_limit(10) == 10
        assert _clamp_limit(5000) == 1000
        assert _clamp_limit("invalid") == 50
        assert _clamp_limit(-5) == 1

    def test_who_entered_zone_success(self, mock_db_connection: Any) -> None:
        """Test who_entered_zone with successful database response"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection

        # Mock database response
        mock_cursor.description = [
            ("track_id",),
            ("resolved_id",),
            ("location_id",),
            ("appear_ms",),
            ("disappear_ms",),
            ("cam_id",),
            ("appear_at_sgt",),
        ]
        mock_cursor.fetchall.return_value = [
            (
                "track_123",
                "person_456",
                "loc_789",
                1609459200000,
                1609459260000,
                "cam_001",
                "2021-01-01 12:00:00",
            )
        ]

        result = who_entered_zone.invoke(
            {
                "location_id": "loc_789",
                "start_ms": 1609459200000,
                "end_ms": 1609459260000,
                "camera_id": "cam_001",
                "limit": 10,
            }
        )

        # Verify database was called with correct parameters
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql_query = call_args[0][0]  # SQL string
        params = call_args[0][1]  # Parameters tuple

        assert "FROM person_sessions" in sql_query
        assert params == ("loc_789", 1609459200000, 1609459260000, "cam_001", 10)

        assert result["ok"] is True
        assert result["count"] == 1
        assert result["rows"][0]["track_id"] == "track_123"
        assert result["filters"]["location_id"] == "loc_789"
        assert result["source"] == "person_sessions"

    def test_who_entered_zone_no_camera_filter(self, mock_db_connection: Any) -> None:
        """Test who_entered_zone without camera filter"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.description = [("track_id",), ("resolved_id",)]
        mock_cursor.fetchall.return_value = []

        result = who_entered_zone.invoke(
            {
                "location_id": "loc_789",
                "start_ms": 1609459200000,
                "end_ms": 1609459260000,
                "limit": 5,
            }
        )

        # Check that camera_id is None in parameters
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]  # Parameters tuple

        assert params[3] is None  # camera_id should be None

        assert result["ok"] is True
        assert result["count"] == 0

    def test_list_anomaly_event_success(self, mock_db_connection: Any) -> None:
        """Test list_anomaly_event with successful database response"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.description = [
            ("ts_ms",),
            ("location_id",),
            ("cam_id",),
            ("incident",),
            ("phase",),
            ("confidence",),
            ("episode",),
            ("ad_event_id",),
            ("end_ms",),
            ("duration_ms",),
            ("ts_at_sgt",),
        ]
        mock_cursor.fetchall.return_value = [
            (
                1609459200000,
                "loc_789",
                "cam_001",
                "intrusion",
                "active",
                0.95,
                "ep_123",
                "event_456",
                1609459260000,
                60000,
                "2021-01-01 12:00:00",
            )
        ]

        result = list_anomaly_event.invoke(
            {
                "start_ms": 1609459200000,
                "end_ms": 1609459260000,
                "location_id": "loc_789",
                "camera_id": "cam_001",
                "limit": 50,
            }
        )

        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]  # Parameters tuple

        assert params == (1609459200000, 1609459260000, "loc_789", "cam_001", 50)

        assert result["ok"] is True
        assert result["count"] == 1
        assert result["rows"][0]["incident"] == "intrusion"

    def test_list_anomaly_event_no_filters(self, mock_db_connection: Any) -> None:
        """Test list_anomaly_event without optional filters"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.description = [("ts_ms",), ("location_id",)]
        mock_cursor.fetchall.return_value = []

        result = list_anomaly_event.invoke(
            {"start_ms": 1609459200000, "end_ms": 1609459260000, "limit": 10}
        )

        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]  # Parameters tuple

        # location_id and camera_id should be None in parameters
        assert params[2] is None  # location_id
        assert params[3] is None  # camera_id

        assert result["ok"] is True
        assert result["filters"]["location_id"] is None
        assert result["filters"]["camera_id"] is None
