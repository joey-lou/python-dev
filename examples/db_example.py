import os

from tools.db_utils import SqliteClient, SqliteInfo

ROOT_PATH = os.path.dirname(__file__)
DB_LOC = os.path.join(ROOT_PATH, "example.db")

with SqliteClient.from_db_info(SqliteInfo(DB_LOC)) as sqlite_client:
    sqlite_client.insert("library", [["Pulp Fiction", "Some Director", 9.0]])
    rows = sqlite_client.get("library")
    for row in rows:
        print(row)
