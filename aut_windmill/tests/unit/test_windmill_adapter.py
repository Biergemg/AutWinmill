import os
import json
import pytest
from unittest.mock import patch
from windmill_automation.adapters.windmill_adapter import EnvWindmillAdapter

def test_get_variable():
    adapter = EnvWindmillAdapter()
    with patch.dict(os.environ, {"WM_VAR_MY_VAR": "secret_value"}):
        assert adapter.get_variable("my_var") == "secret_value"
        assert adapter.get_variable("non_existent") is None

def test_get_resource():
    adapter = EnvWindmillAdapter()
    res_data = {"host": "localhost", "port": 5432}
    with patch.dict(os.environ, {"WM_RES_DB_CONFIG": json.dumps(res_data)}):
        assert adapter.get_resource("db_config") == res_data
        assert adapter.get_resource("non_existent") == {}
        
def test_get_resource_invalid_json():
    adapter = EnvWindmillAdapter()
    with patch.dict(os.environ, {"WM_RES_BAD_JSON": "{invalid"}):
        assert adapter.get_resource("bad_json") == {}
