import pytest

from app.settings import read_bool_env, read_float_env


def test_read_bool_env_returns_default_when_missing(monkeypatch):
    monkeypatch.delenv("TEMP_TEST_BOOL", raising=False)

    assert read_bool_env("TEMP_TEST_BOOL", default=False) is False
    assert read_bool_env("TEMP_TEST_BOOL", default=True) is True


def test_read_bool_env_accepts_true_values(monkeypatch):
    true_values = [
        "1",
        "true",
        "TRUE",
        "yes",
        "y",
        "on",
    ]

    for value in true_values:
        monkeypatch.setenv("TEMP_TEST_BOOL", value)
        assert read_bool_env("TEMP_TEST_BOOL", default=False) is True


def test_read_bool_env_accepts_false_values(monkeypatch):
    false_values = [
        "0",
        "false",
        "FALSE",
        "no",
        "n",
        "off",
    ]

    for value in false_values:
        monkeypatch.setenv("TEMP_TEST_BOOL", value)
        assert read_bool_env("TEMP_TEST_BOOL", default=True) is False


def test_read_bool_env_rejects_invalid_value(monkeypatch):
    monkeypatch.setenv("TEMP_TEST_BOOL", "maybe")

    with pytest.raises(RuntimeError, match="Invalid boolean value"):
        read_bool_env("TEMP_TEST_BOOL", default=False)


def test_read_float_env_returns_default_when_missing(monkeypatch):
    monkeypatch.delenv("TEMP_TEST_FLOAT", raising=False)

    assert read_float_env("TEMP_TEST_FLOAT", default=8.0) == 8.0


def test_read_float_env_reads_valid_number(monkeypatch):
    monkeypatch.setenv("TEMP_TEST_FLOAT", "5.5")

    assert read_float_env("TEMP_TEST_FLOAT", default=8.0) == 5.5


def test_read_float_env_rejects_non_numeric_value(monkeypatch):
    monkeypatch.setenv("TEMP_TEST_FLOAT", "abc")

    with pytest.raises(RuntimeError, match="Invalid numeric value"):
        read_float_env("TEMP_TEST_FLOAT", default=8.0)


def test_read_float_env_rejects_zero_or_negative_value(monkeypatch):
    monkeypatch.setenv("TEMP_TEST_FLOAT", "0")

    with pytest.raises(RuntimeError, match="greater than 0"):
        read_float_env("TEMP_TEST_FLOAT", default=8.0)

    monkeypatch.setenv("TEMP_TEST_FLOAT", "-1")

    with pytest.raises(RuntimeError, match="greater than 0"):
        read_float_env("TEMP_TEST_FLOAT", default=8.0)