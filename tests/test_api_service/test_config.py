"""
Test Configuration Module

Tests for API configuration loading and validation.
"""

from api_service.config import APIConfig, get_api_config


class TestConfigLoading:
    """Test configuration loading"""

    def test_get_api_config_returns_instance(self):
        """
        Test that get_api_config returns APIConfig instance

        Expected: APIConfig object
        """
        config = get_api_config()

        assert isinstance(config, APIConfig)
        print("✓ Config loaded successfully")

    def test_config_has_required_fields(self):
        """
        Test configuration has all required fields

        Expected: All required fields present
        """
        config = get_api_config()

        # Check required fields exist
        assert hasattr(config, "SECRET_KEY")
        assert hasattr(config, "ALGORITHM")
        assert hasattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert hasattr(config, "HOST")
        assert hasattr(config, "PORT")
        assert hasattr(config, "V1_PREFIX")
        assert hasattr(config, "PROJECT_NAME")
        assert hasattr(config, "VERSION")
        assert hasattr(config, "ALLOWED_ORIGINS")

        print("✓ All required fields present")

    def test_config_field_types(self):
        """Test configuration fields have correct types"""
        config = get_api_config()

        assert isinstance(config.SECRET_KEY, str)
        assert isinstance(config.ALGORITHM, str)
        assert isinstance(config.ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert isinstance(config.HOST, str)
        assert isinstance(config.PORT, int)
        assert isinstance(config.V1_PREFIX, str)
        assert isinstance(config.PROJECT_NAME, str)
        assert isinstance(config.VERSION, str)
        assert isinstance(config.ALLOWED_ORIGINS, list)
        assert isinstance(config.DEBUG, bool)

        print("✓ All fields have correct types")

    def test_config_field_values(self):
        """Test configuration fields have valid values"""
        config = get_api_config()

        # Port should be valid
        assert config.PORT > 0
        assert config.PORT < 65536

        # Host should not be empty
        assert len(config.HOST) > 0

        # V1_PREFIX should start with /
        assert config.V1_PREFIX.startswith("/")

        # Algorithm should be valid
        assert config.ALGORITHM in ["HS256", "HS384", "HS512", "RS256"]

        # Expiry should be positive
        assert config.ACCESS_TOKEN_EXPIRE_MINUTES > 0

        print("✓ All field values valid")
        print(f"  Port: {config.PORT}")
        print(f"  Host: {config.HOST}")
        print(f"  Algorithm: {config.ALGORITHM}")
        print(f"  Token Expiry: {config.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

    def test_config_caching(self):
        """
        Test that configuration is cached (singleton pattern)

        Expected: Same instance returned on multiple calls
        """
        config1 = get_api_config()
        config2 = get_api_config()

        # Should be the exact same instance
        assert config1 is config2
        print("✓ Config is cached (singleton)")

    def test_config_allowed_origins_is_list(self):
        """Test ALLOWED_ORIGINS is a list of strings"""
        config = get_api_config()

        assert isinstance(config.ALLOWED_ORIGINS, list)
        assert len(config.ALLOWED_ORIGINS) > 0

        for origin in config.ALLOWED_ORIGINS:
            assert isinstance(origin, str)
            assert origin.startswith("http")

        print(f"✓ Allowed origins: {config.ALLOWED_ORIGINS}")

    def test_config_environment_settings(self):
        """Test environment-related settings"""
        config = get_api_config()

        assert hasattr(config, "ENVIRONMENT")
        assert hasattr(config, "LOG_LEVEL")

        assert config.ENVIRONMENT in ["development", "staging", "production", "test"]
        assert config.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        print(f"✓ Environment: {config.ENVIRONMENT}")
        print(f"✓ Log Level: {config.LOG_LEVEL}")
