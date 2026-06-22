import pytest

from backend.core.config import get_runtime_settings


def test_runtime_settings_defaults_preserve_testserver(monkeypatch) -> None:
    for name in [
        "APP_ENV",
        "LOG_LEVEL",
        "TRUSTED_HOSTS",
        "SECURITY_HEADERS_ENABLED",
        "READINESS_REQUIRE_DATABASE",
        "READINESS_REQUIRE_REDIS",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_runtime_settings()

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.trusted_hosts == ("localhost", "127.0.0.1", "testserver")
    assert settings.security_headers_enabled is True
    assert settings.readiness_require_database is False
    assert settings.readiness_require_redis is False


def test_runtime_settings_validates_log_level(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "warning")
    assert get_runtime_settings().log_level == "WARNING"

    monkeypatch.setenv("LOG_LEVEL", "LOUD")
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        get_runtime_settings()


def test_runtime_settings_parses_booleans(monkeypatch) -> None:
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "off")
    monkeypatch.setenv("READINESS_REQUIRE_DATABASE", "yes")
    monkeypatch.setenv("READINESS_REQUIRE_REDIS", "0")

    settings = get_runtime_settings()

    assert settings.security_headers_enabled is False
    assert settings.readiness_require_database is True
    assert settings.readiness_require_redis is False

    monkeypatch.setenv("READINESS_REQUIRE_REDIS", "maybe")
    with pytest.raises(ValueError, match="READINESS_REQUIRE_REDIS"):
        get_runtime_settings()


def test_runtime_settings_trims_and_deduplicates_trusted_hosts(monkeypatch) -> None:
    monkeypatch.setenv("TRUSTED_HOSTS", " localhost, api,localhost,,api ")

    settings = get_runtime_settings()

    assert settings.trusted_hosts == ("localhost", "api", "testserver")
