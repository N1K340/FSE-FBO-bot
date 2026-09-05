import json
import ast
from typing import Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# FBO Tanks
# Tank Size | Capacity | Safe Fill | Order Trigger | Order Ammount
#   10ft    | 3,170 g  | 2,950 usg | 1,770 usg     | 5,000kg
#   20ft    | 10,038 g | 9,300 usg | 5,580 usg     | 10,000kg
#   30ft    | 17,964 g | 16,740 usg| 9,300 usg     | 15,000kg

class Settings(BaseSettings):
    TEST_MODE: bool = Field(default=False, validation_alias="TEST_MODE")

    # FBO Thresholds
    supplies_threshold: int = 5  # Days
    DEFAULT_AVGAS_THRESHOLD: int = 1770  # Default small strip Avgas limit
    DEFAULT_JET_THRESHOLD: int = 5580   # Default to 20ft tank limit (15k kg)

    TANK_THRESHOLDS: Dict[str, int] = {
        "10ft": 1770,   # Top up 5,000 kg
        "20ft": 5580,  # Top up 10,000 kg
        "40ft": 9300,  # Top up 15,000 kg
    }

    # Environment Credentials & Webhooks
    fbohook_url: str = Field(default="Not Set", validation_alias="FBOHOOK")
    mxhook_url: str = Field(default="Not Set", validation_alias="MXHOOK")
    fse_username: str = Field(default="", validation_alias="FSE_USERNAME")  # Web login username
    fse_user_key: str = Field(default="", validation_alias="FSE_USER_KEY")   # User API key
    fsepassword: str = Field(default="", validation_alias="FSEPASSWORD")

    fsegroup1: str = Field(default="", validation_alias="FSEGROUP1")
    fsegroup2: str = Field(default="", validation_alias="FSEGROUP2")

    # Bank Accounts & Buffer Configuration
    PERSONAL_ACC_ID: str = Field(default="", validation_alias="PERSONAL_ACC_ID")  # Personal Account
    AIRCRAFT_ACC_ID: str = Field(default="", validation_alias="AIRCRAFT_ACC_ID")  # Aircraft Holding Account
    MAINT_ACC_ID: str = Field(default="", validation_alias="MAINT_ACC_ID")  # Maintenance fund Account
    AIRCRAFT_ACC_NAME: str = Field(default="", validation_alias="AIRCRAFT_ACC_NAME")  # Aircraft Holding Account
    MAINT_ACC_NAME: str = Field(default="", validation_alias="MAINT_ACC_NAME")  # Maintenance fund Account

    monthly_buffer: float = Field(default=10000.00, validation_alias="MONTHLY_BUFFER")

    # Complex Structures
    aircraft: Any = Field(default_factory=dict, validation_alias="AIRCRAFT")
    fbo_overrides: Any = Field(default_factory=dict, validation_alias="FBO_OVERRIDES")
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("aircraft", "fbo_overrides", mode="before")
    @classmethod
    def parse_dict_string(cls, value: Any) -> Dict[str, Any]:
        """Supports both standard JSON strings and Python dict literal strings."""
        if isinstance(value, str):
            if not value.strip():
                return {}
            # Try JSON parsing first
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Fall back to Python literal evaluation
                try:
                    return ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    return {}
        return value if isinstance(value, dict) else {}

# Instantiate module-level singleton matching existing package imports
settings = Settings()