from fratelanza.infrastructure.database.schema_manager import split_sql_batches


def test_split_sql_batches_handles_go_separators() -> None:
    sql = """
    SELECT 1
    GO
    SELECT 2
    go;
    """

    assert split_sql_batches(sql) == ["SELECT 1", "SELECT 2"]
