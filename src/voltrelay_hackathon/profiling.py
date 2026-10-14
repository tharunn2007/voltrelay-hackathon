import duckdb

def profile_table(con: duckdb.DuckDBPyConnection, table: str, pk_cols: list[str] | None = None):
    schema = con.sql(f"DESCRIBE {table}").df()
    n_rows = con.sql(f"SELECT count(*) FROM {table}").fetchone()[0]
    print(f"\n=== {table} ({n_rows:,} rows, {len(schema)} cols) ===")

    null_pct = con.sql(f"""
        SELECT {", ".join(
            f"round(100.0 * sum(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) / count(*), 2) AS {c}"
            for c in schema['column_name']
        )}
        FROM {table}
    """).df().T
    null_pct.columns = ["null_pct"]
    print(null_pct[null_pct["null_pct"] > 0])

    if pk_cols:
        dupe_count = con.sql(f"""
            SELECT count(*) FROM (
                SELECT {", ".join(pk_cols)}, count(*) c
                FROM {table} GROUP BY {", ".join(pk_cols)} HAVING c > 1
            )
        """).fetchone()[0]
        print(f"Duplicate {pk_cols}: {dupe_count}")

    return schema