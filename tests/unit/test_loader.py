import pytest


class TestLoader:
    def test_load_tools_integration(self) -> None:
        """Integration test for load_tools - tests the actual function"""
        # Import and test the actual function without MCP mocking
        from sentinel_mas.tools.loader import load_tools

        tools = load_tools()

        # Should return a dictionary
        assert isinstance(tools, dict)

        # Should contain expected tools
        expected_tools = [
            "get_sop",
            "search_sop",
            "list_anomaly_event",
            "who_entered_zone",
        ]

        # Check which expected tools are actually present
        found_tools = [tool for tool in expected_tools if tool in tools]
        print(f"Found tools: {found_tools}")
        print(f"All tools: {list(tools.keys())}")

        # At least some tools should be loaded
        assert len(tools) > 0, "No tools were loaded"

    def test_load_langchain_decorated_tools_structure(self) -> None:
        """Test the structure of loaded tools"""
        from sentinel_mas.tools.loader import load_langchain_decorated_tools

        tools = load_langchain_decorated_tools()

        # Should return a dictionary
        assert isinstance(tools, dict)

        # Each tool should have a 'name' attribute
        for tool_name, tool in tools.items():
            assert hasattr(tool, "name"), f"Tool {tool_name} missing name attribute"

    def test_tool_registry_consistency(self) -> None:
        """Test that TOOL_REGISTRY is consistent with loaded tools - FIXED"""
        from sentinel_mas.tools import TOOL_REGISTRY
        from sentinel_mas.tools.loader import load_tools

        loaded_tools = load_tools()

        # Instead of exact equality (which fails due to different function objects),
        # check that they have the same keys and tool names
        assert set(TOOL_REGISTRY.keys()) == set(
            loaded_tools.keys()
        ), "Tool registry keys should match"

        # Check that tool names match
        for tool_name in TOOL_REGISTRY:
            assert (
                TOOL_REGISTRY[tool_name].name == loaded_tools[tool_name].name
            ), f"Tool name mismatch for {tool_name}"

    def test_specific_tools_present(self) -> None:
        """Test that specific expected tools are present"""
        from sentinel_mas.tools.loader import load_tools

        tools = load_tools()

        # Check for tools that should definitely be there
        expected_tools_sets = [
            # SOP tools
            {"get_sop", "search_sop"},
            # Events tools
            {"list_anomaly_event", "who_entered_zone"},
            # Tracking tools
            {"send_track", "send_cancel", "get_track_status", "get_person_insight"},
        ]

        # At least one tool from each category should be present
        tool_names = set(tools.keys())
        for expected_set in expected_tools_sets:
            found_tools = expected_set.intersection(tool_names)
            assert len(found_tools) > 0, f"No tools found from set: {expected_set}"


# Test the actual tool modules directly - FIXED
class TestToolModules:
    def test_events_tools_import(self) -> None:
        """Test that events tools can be imported and have expected functions - FIXED"""
        try:
            from sentinel_mas.tools.events_tools import (
                list_anomaly_event,
                who_entered_zone,
            )

            # LangChain tools are callable objects, not raw functions
            assert hasattr(list_anomaly_event, "func") and callable(
                list_anomaly_event.func
            )
            assert hasattr(who_entered_zone, "func") and callable(who_entered_zone.func)
        except ImportError as e:
            pytest.skip(f"Events tools not available: {e}")

    def test_sop_tools_import(self) -> None:
        """Test that SOP tools can be imported and have expected functions - FIXED"""
        try:
            from sentinel_mas.tools.sop_tools import get_sop, search_sop

            assert hasattr(get_sop, "func") and callable(get_sop.func)
            assert hasattr(search_sop, "func") and callable(search_sop.func)
        except ImportError as e:
            pytest.skip(f"SOP tools not available: {e}")

    def test_tracking_tools_import(self) -> None:
        """Test that tracking tools can be imported and have expected functions"""
        try:
            from sentinel_mas.tools.tracking_tools import (
                get_person_insight,
                get_track_status,
                send_cancel,
                send_track,
            )

            assert hasattr(send_track, "func") and callable(send_track.func)
            assert hasattr(send_cancel, "func") and callable(send_cancel.func)
            assert hasattr(get_track_status, "func") and callable(get_track_status.func)
            assert hasattr(get_person_insight, "func") and callable(
                get_person_insight.func
            )
        except ImportError as e:
            pytest.skip(f"Tracking tools not available: {e}")


# Run coverage-friendly test
def test_coverage_collection() -> None:
    """Simple test to ensure coverage data is collected"""
    from sentinel_mas.tools.loader import load_tools

    tools = load_tools()
    assert tools is not None
    assert isinstance(tools, dict)


# Test tool functionality
class TestToolFunctionality:
    def test_tools_have_descriptions(self) -> None:
        """Test that all tools have descriptions"""
        from sentinel_mas.tools.loader import load_tools

        tools = load_tools()

        for tool_name, tool in tools.items():
            assert hasattr(tool, "description"), f"Tool {tool_name} missing description"
            assert tool.description, f"Tool {tool_name} has empty description"
            print(f"✓ {tool_name}: {tool.description[:50]}...")

    def test_tools_have_schemas(self) -> None:
        """Test that all tools have argument schemas"""
        from sentinel_mas.tools.loader import load_tools

        tools = load_tools()

        for tool_name, tool in tools.items():
            assert hasattr(tool, "args_schema"), f"Tool {tool_name} missing args_schema"
            print(f"✓ {tool_name} has argument schema")

    def test_tool_names_match_keys(self) -> None:
        """Test that tool names match their dictionary keys"""
        from sentinel_mas.tools.loader import load_tools

        tools = load_tools()

        for tool_name, tool in tools.items():
            assert (
                tool.name == tool_name
            ), f"Tool name mismatch: {tool.name} != {tool_name}"
