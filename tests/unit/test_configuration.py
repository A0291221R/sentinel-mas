# tests/test_configuration_real_tools.py
import pytest
import yaml
import tempfile
import os
from unittest.mock import patch, MagicMock

from sentinel_mas.agents.loader import load_agent_configs


class TestConfigurationRealTools:
    """Tests using the actual tool names from your system"""
    
    def test_router_agent_config_loading(self):
        """Test loading router agent config (no tools)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_config = {
                'name': 'router_agent',
                'llm': {
                    'model': 'gpt-4o-mini',
                    'temperature': 0.0,
                    'max_tokens': 64
                },
                'tools': [],  # Router has no tools
                'system_prompt': 'You are the router agent.'
            }
            
            config_path = os.path.join(temp_dir, 'router_agent.yml')
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            with patch('sentinel_mas.agents.loader.TOOL_REGISTRY', {}):
                agent_registry = load_agent_configs(temp_dir)
                
                assert 'router_agent' in agent_registry
                runtime = agent_registry['router_agent']
                assert runtime.name == 'router_agent'
                assert runtime.llm_max_tokens == 64
                assert runtime.tools == {}  # No tools
    
    def test_faq_agent_config_loading(self):
        """Test loading FAQ agent config with SOP tools"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_config = {
                'name': 'faq_agent',
                'llm': {
                    'model': 'gpt-4o-mini',
                    'temperature': 0.0,
                    'max_tokens': 350
                },
                'tools': ['get_sop', 'search_sop'],
                'system_prompt': 'You are the FAQ agent.'
            }
            
            config_path = os.path.join(temp_dir, 'faq_agent.yml')
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Mock the exact tools that FAQ agent needs
            mock_tool_registry = {
                'get_sop': MagicMock(),
                'search_sop': MagicMock()
            }
            
            with patch('sentinel_mas.agents.loader.TOOL_REGISTRY', mock_tool_registry):
                agent_registry = load_agent_configs(temp_dir)
                
                assert 'faq_agent' in agent_registry
                runtime = agent_registry['faq_agent']
                assert runtime.name == 'faq_agent'
                assert len(runtime.tools) == 2
                assert 'get_sop' in runtime.tools
                assert 'search_sop' in runtime.tools
    
    def test_events_agent_config_loading(self):
        """Test loading events agent config with event tools"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_config = {
                'name': 'events_agent',
                'llm': {
                    'model': 'gpt-4o-mini',
                    'temperature': 0.0,
                    'max_tokens': 1300
                },
                'tools': ['who_entered_zone', 'list_anomaly_event'],
                'system_prompt': 'You are the events agent.'
            }
            
            config_path = os.path.join(temp_dir, 'events_agent.yml')
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Mock the exact tools that events agent needs
            mock_tool_registry = {
                'who_entered_zone': MagicMock(),
                'list_anomaly_event': MagicMock()
            }
            
            with patch('sentinel_mas.agents.loader.TOOL_REGISTRY', mock_tool_registry):
                agent_registry = load_agent_configs(temp_dir)
                
                assert 'events_agent' in agent_registry
                runtime = agent_registry['events_agent']
                assert runtime.name == 'events_agent'
                assert runtime.llm_max_tokens == 1300
                assert len(runtime.tools) == 2
                assert 'who_entered_zone' in runtime.tools
                assert 'list_anomaly_event' in runtime.tools
    
    def test_tracking_agent_config_loading(self):
        """Test loading tracking agent config with tracking tools"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_config = {
                'name': 'tracking_agent',
                'llm': {
                    'model': 'gpt-4o-mini',
                    'temperature': 0.0,
                    'max_tokens': 300
                },
                'tools': ['send_track', 'send_cancel', 'get_track_status', 'get_person_insight'],
                'system_prompt': 'You are the tracking agent.'
            }
            
            config_path = os.path.join(temp_dir, 'tracking_agent.yml')
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Mock the exact tools that tracking agent needs
            mock_tool_registry = {
                'send_track': MagicMock(),
                'send_cancel': MagicMock(),
                'get_track_status': MagicMock(),
                'get_person_insight': MagicMock()
            }
            
            with patch('sentinel_mas.agents.loader.TOOL_REGISTRY', mock_tool_registry):
                agent_registry = load_agent_configs(temp_dir)
                
                assert 'tracking_agent' in agent_registry
                runtime = agent_registry['tracking_agent']
                assert runtime.name == 'tracking_agent'
                assert len(runtime.tools) == 4
                assert 'send_track' in runtime.tools
                assert 'get_person_insight' in runtime.tools