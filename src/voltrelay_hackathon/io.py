from pathlib import Path
import duckdb

TABLES = ["batteries", "stations", "riders", "support_tickets",
          "city_daily_context", "fleet_partners", "swap_events", "station_hourly_status"]

SWAP_EVENTS_SCHEMA = {
    "event_id": "VARCHAR", "rider_id": "VARCHAR", "station_id": "VARCHAR",
    "event_ts": "TIMESTAMP", "event_type": "VARCHAR", "attempt_seq": "INTEGER",
    "queue_wait_sec": "INTEGER", "battery_in_id": "VARCHAR", "battery_out_id": "VARCHAR",
    "soc_in_pct": "DOUBLE", "soh_in_pct": "DOUBLE", "soc_out_pct": "DOUBLE",
    "soh_out_pct": "DOUBLE", "km_since_last_swap": "DOUBLE", "tariff_code": "VARCHAR",
    "list_price_inr": "DOUBLE", "discount_inr": "DOUBLE", "amount_charged_inr": "DOUBLE",
    "payment_mode": "VARCHAR", "energy_to_recharge_kwh": "DOUBLE",
    "station_firmware": "VARCHAR", "sync_mode": "VARCHAR",
}


def load_tables(data_dir: str = "data") -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection with one view per CSV."""
    con = duckdb.connect()
    data = Path(data_dir)
    for t in TABLES:
        if t == "swap_events":
            con.execute(f"""
                CREATE OR REPLACE VIEW {t} AS
                SELECT * FROM read_csv(
                    '{data/t}.csv', header=true, delim=',', quote='"', escape='"',
                    columns={SWAP_EVENTS_SCHEMA}, auto_detect=false,
                    ignore_errors=true, strict_mode=false, max_line_size=10000000
                )
            """)
        else:
            con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_csv_auto('{data/t}.csv')")
    return con