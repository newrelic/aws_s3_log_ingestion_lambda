import unittest
from src.handler import _get_log_type

def test_get_log_type_with_parameter():
    assert _get_log_type("PARAMETER") == "PARAMETER"

def test_get_log_type_env_var(monkeypatch):
    monkeypatch.setenv("LOG_TYPE", "ENV_VAR")
    assert _get_log_type() == "ENV_VAR"

def test_get_log_type_alt_env_var(monkeypatch):
    monkeypatch.setenv("LOGTYPE", "ALT_ENV_VAR")
    assert _get_log_type() == "ALT_ENV_VAR"
