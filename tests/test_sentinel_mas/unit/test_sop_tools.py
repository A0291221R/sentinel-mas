import pytest

from sentinel_mas.tools.sop_tools import get_sop, search_sop


class TestSOPTools:

    def test_search_sop_success(self, mock_db_connection, mock_embedding) -> None:
        """Test search_sop with successful database response"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection

        # Mock database response for vector search
        mock_cursor.fetchall.return_value = [
            ("SOP-1", "1.1", "Emergency Procedures", "Emergency text...", 0.95)
        ]

        result = search_sop.invoke({"query": "emergency procedures", "k": 5})

        # Verify embedding was called
        mock_embedding.assert_called_once_with("emergency procedures")

        # Verify database query was executed
        mock_cursor.execute.assert_called_once()

        # Check the SQL call parameters - call_args is (args, kwargs)
        call_args = mock_cursor.execute.call_args
        sql_query = call_args[0][0]  # First argument is SQL string
        params = call_args[0][1]  # Second argument is parameters tuple

        assert "SELECT id, section, title, text" in sql_query
        assert params == ([0.1, 0.2, 0.3], [0.1, 0.2, 0.3], 5)  # Check parameters

        # Verify result structure
        assert len(result) == 1
        assert result[0]["id"] == "SOP-1"
        assert result[0]["section"] == "1.1"
        assert result[0]["title"] == "Emergency Procedures"
        assert result[0]["text"] == "Emergency text..."
        assert result[0]["cos_sim"] == 0.95

    def test_search_sop_default_k(self, mock_db_connection, mock_embedding) -> None:
        """Test search_sop with default k value"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []

        result = search_sop.invoke({"query": "test query"})

        # Should use default k=6
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]  # Second argument is parameters tuple

        # The LIMIT parameter is the third element in the params tuple
        assert params[2] == 6  # LIMIT parameter should be 6 (default)

        assert result == []  # Empty result

    def test_search_sop_custom_k(self, mock_db_connection, mock_embedding) -> None:
        """Test search_sop with custom k value"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []

        result = search_sop.invoke({"query": "test query", "k": 10})

        # Should use custom k=10
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]  # Second argument is parameters tuple

        assert params[2] == 10  # LIMIT parameter should be 10

        assert result == []

    def test_get_sop_by_id_success(self, mock_db_connection) -> None:
        """Test get_sop with valid SOP ID"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = (
            "SOP-1",
            "1.1",
            "Test Procedure",
            "Detailed text...",
            '["emergency", "safety"]',
            "2023-01-01 12:00:00",
            None,
        )

        result = get_sop.invoke({"id_or_section": "SOP-1"})

        # Verify database query
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql_query = call_args[0][0]  # SQL string
        params = call_args[0][1]  # Parameters tuple

        assert "SELECT id, section, title, text, tags, updated_at" in sql_query
        assert params == ("SOP-1", "SOP-1")  # Both parameters should be the same

        # Verify result structure
        assert result is not None
        assert result["id"] == "SOP-1"
        assert result["section"] == "1.1"
        assert result["title"] == "Test Procedure"
        assert result["text"] == "Detailed text..."
        assert "emergency" in result["tags"]
        assert result["updated_at"] == "2023-01-01 12:00:00"
        assert result["full"] is None

    def test_get_sop_by_section_success(self, mock_db_connection) -> None:
        """Test get_sop with valid section number"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = (
            "SOP-2",
            "2.3",
            "Another Procedure",
            "More text...",
            None,
            "2023-01-01 12:00:00",
            None,
        )

        result = get_sop.invoke({"id_or_section": "2.3"})

        # Verify database query
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]  # Parameters tuple

        assert params == ("2.3", "2.3")  # Both parameters should be the section

        assert result is not None
        assert result["id"] == "SOP-2"
        assert result["section"] == "2.3"
        assert result["title"] == "Another Procedure"
        assert result["tags"] is None

    def test_get_sop_not_found(self, mock_db_connection) -> None:
        """Test get_sop with non-existent ID/section"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None

        result = get_sop.invoke({"id_or_section": "NON_EXISTENT"})

        # Verify database was queried
        mock_cursor.execute.assert_called_once()

        assert result is None

    def test_search_sop_database_error(
        self, mock_db_connection, mock_embedding
    ) -> None:
        """Test search_sop handles database errors gracefully"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection
        mock_cursor.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            search_sop.invoke({"query": "test query", "k": 5})

        assert "Database connection failed" in str(exc_info.value)

    def test_get_sop_database_error(self, mock_db_connection) -> None:
        """Test get_sop handles database errors gracefully"""
        mock_connect, mock_conn, mock_cursor = mock_db_connection
        mock_cursor.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            get_sop.invoke({"id_or_section": "SOP-1"})

        assert "Database connection failed" in str(exc_info.value)
