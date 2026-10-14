import pandas as pd
from .config import CITY_MAP

FW_BUG_START = pd.Timestamp("2025-03-10")
FW_BUG_END = pd.Timestamp("2025-04-15")   # exclusive, so Apr 14 is included
FW_BUG_SHIFT = pd.Timedelta(hours=5, minutes=30)


def normalize_city(series: pd.Series) -> pd.Series:
    cleaned = series.str.strip().str.lower()
    mapped = cleaned.map(CITY_MAP)
    unmapped = series[mapped.isna() & series.notna()].unique()
    if len(unmapped):
        raise ValueError(f"Unmapped city values found, update CITY_MAP: {unmapped}")
    return mapped


def fix_firmware_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """v3.2.0 stations logged event_ts 5h30m early between Mar 10 and Apr 14, 2025."""
    df = df.copy()
    df["event_ts_raw"] = df["event_ts"]
    in_bug = (
        (df["station_firmware"] == "v3.2.0")
        & (df["event_ts"] >= FW_BUG_START)
        & (df["event_ts"] < FW_BUG_END)
    )
    df["flag_ts_corrected"] = in_bug
    df.loc[in_bug, "event_ts"] = df.loc[in_bug, "event_ts"] + FW_BUG_SHIFT
    return df


def flag_pre_commission_events(events_df, stations_df):
    """Validation check: should flag 0 rows once timestamps are corrected."""
    merged = events_df.merge(
        stations_df[["station_id", "commissioned_date", "firmware_version"]],
        on="station_id", how="left",
    )
    merged["flag_pre_commission_timestamp"] = (
        (merged["event_ts"].dt.date < merged["commissioned_date"])
        & (merged["firmware_version"] == "v3.2.0")
    )
    return merged


def flag_impossible_battery_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["flag_soh_over_100"] = (df["soh_in_pct"] > 100) | (df["soh_out_pct"] > 100)
    df["flag_soc_over_100"] = (df["soc_in_pct"] > 100) | (df["soc_out_pct"] > 100)
    df["flag_negative_km"] = df["km_since_last_swap"] < 0
    return df


def flag_near_duplicate_events(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    dupe_key = df["rider_id"] + "_" + df["station_id"] + "_" + df["event_ts"].astype(str)
    df["flag_exact_duplicate"] = dupe_key.duplicated(keep=False)
    return df


def clean_swap_events(swap_df, stations_df):
    df = fix_firmware_timestamps(swap_df)
    df = flag_pre_commission_events(df, stations_df)   # should now flag 0 rows
    df = flag_impossible_battery_values(df)
    df = flag_near_duplicate_events(df)
    return df