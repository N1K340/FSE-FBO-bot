# fse_pipeline/analytics.py
import datetime
import pandas as pd
from fse_pipeline.config import settings

# FBO Analytics

def get_supply_warnings(df: pd.DataFrame) -> pd.DataFrame:
    """Returns FBOs with supply days below threshold."""
    return df[df["SuppliedDays"] < settings.supplies_threshold]

def _resolve_threshold(airport_code: str, fuel_type: str, global_default: int) -> int:
    """Helper to resolve whether an override is a tank size name or a raw number."""
    print(f"Looking up airport: '{airport_code}")
    airport_config = settings.fbo_overrides.get(airport_code, {})
    val = airport_config.get(fuel_type)
    
    if val is None:
        return global_default
    
    # If they passed a tank size string like '40ft', look it up in our dictionary
    if isinstance(val, str) and val in settings.TANK_THRESHOLDS:
        return settings.TANK_THRESHOLDS[val]
    
    # Otherwise, assume it's a raw integer/number override
    try:
        return int(val)
    except (ValueError, TypeError):
        return global_default

def get_jeta_warnings(df: pd.DataFrame) -> pd.DataFrame:
    """Evaluates Jet-A using container tank limits or global defaults."""
    def get_threshold(row):
        return _resolve_threshold(row["Icao"], "jet", settings.DEFAULT_JET_THRESHOLD)

    df = df.copy()
    df["CustomJetThreshold"] = df.apply(get_threshold, axis=1)
    
    return df[(df["FuelJetA"] < df["CustomJetThreshold"]) & (df["PriceJetAGal"] > 0)]

def get_avgas_warnings(df: pd.DataFrame) -> pd.DataFrame:
    """Evaluates Avgas using container tank limits or global defaults."""
    def get_threshold(row):
        return _resolve_threshold(row["Icao"], "avgas", settings.DEFAULT_AVGAS_THRESHOLD)

    df = df.copy()
    df["CustomAvgasThreshold"] = df.apply(get_threshold, axis=1)
    
    return df[(df["Fuel100LL"] < df["CustomAvgasThreshold"]) & (df["Price100LLGal"] > 0)]

# Aircraft Analytics
def calc_target_date() -> tuple[str, str]:
    """Returns the target month ('01'-'12') and year ('YYYY') for the previous month."""
    today = datetime.date.today()
    first_of_month = today.replace(day=1)
    last_month = first_of_month - datetime.timedelta(days=1)
    return last_month.strftime("%m"), last_month.strftime("%Y")

def _convert_dec(time_str: str):
    """Converts a 'HH:MM' string to decimal hours."""
    try:
        hours, minutes = map(int, str(time_str).split(":"))
        return hours + (minutes / 60)
    except (ValueError):
        return 0.0

def calculate_aircraft_lease_cost(df: pd.DataFrame, cost_per_hour: float) -> tuple[float, float]:
    """Calculates total flight hours and total cost for a specific aircraft log dataframe.
    
    Returns:
        tuple: (total_hours, total_cost)
    """
    if df.empty or "FlightTime" not in df.columns:
        return 0.0, 0.0

    df = df.copy()
    df["DecTime"] = df["FlightTime"].apply(_convert_dec)
    
    total_hrs = round(df["DecTime"].sum(), 1)
    total_cost = round(total_hrs * cost_per_hour, 2)
    
    return total_hrs, total_cost

def calculate_monthly_aircraft_fees(df: pd.DataFrame) -> float:
    """Calculates sum of monthly aircraft costs from aircraft by key datafeed."""
    if df.empty:
        return 0.0
    fee_cols = [col for col in df.columns if "monthly" in col.lower()]
    if fee_cols:
        return float(df[fee_cols[0]].sum())
    return 0.0

def get_account_balance(df: pd.DataFrame) -> float:
    """Extracts available cash balance (Personal_balance) from statistics datafeed."""
    if df.empty or "Personal_balance" not in df.columns:
        return 0.0
    return float(df["Personal_balance"].iloc[0])