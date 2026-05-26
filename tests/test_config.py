from unittest.mock import patch

from fratelanza.core import config


def test_resolve_sql_server_driver_prefers_installed_driver() -> None:
    class FakePyodbc:
        @staticmethod
        def drivers() -> list[str]:
            return ["SQL Server", "ODBC Driver 17 for SQL Server"]

    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "pyodbc":
            return FakePyodbc
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", fake_import):
        assert (
            config.resolve_sql_server_driver("ODBC Driver 18 for SQL Server")
            == "ODBC Driver 17 for SQL Server"
        )
