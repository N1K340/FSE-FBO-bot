# FSE-FBO-bot

Python bot designed to monitor FSEconomy FBO holdings, fuel inventory, automated monthly operations, and aircraft maintenance costs.

## Features

- **Startup API Validation**: Validates User Key and Group Keys against FSE Economy XML endpoints before entering execution loop. Aggregates and logs any failed keys on startup.
- **FBO Supply Monitoring**: Warns when FBO supply inventory falls below specified day threshold.
- **Fuel Inventory Checks**: Monitors JetA and Avgas levels against minimum thresholds for FBOs actively selling fuel (fuel price > $1).
- **Monthly Operations & Transfers**: Generates monthly FBO reports and automates configured fund transfers.
- **Aircraft Maintenance Tracking**: Tracks monthly aircraft flight hours and calculates amortized maintenance costs based on hourly rates.
- **Discord Webhooks**: Sends separate notifications for FBO operations and aircraft maintenance checks directly to Discord channels.

## Project Structure

```text
.
├── main.py                   # Entry point and schedule runner
├── fse_pipeline/
│   ├── fse_api.py            # FSE Economy API queries and XML response parsing
│   ├── analytics.py          # FBO supply and aircraft maintenance calculations
│   └── config.py             # Configuration settings and environment variables
├── requirements.txt          # Dependencies
└── compose.yaml              # Docker Compose configuration
```

## Setup and Deployment

This application is designed to run in a Docker container (e.g., via Docker Compose or Dockge).

### Environment Variables

Set the following variables in your `.env` file or container environment:

# ==========================================
# FSE-FBO-Bot Environment Configuration
# ==========================================

# Execution Mode
TEST_MODE=False

# FSE Credentials & API Keys
FSE_USERNAME=""
FSEPASSWORD=""
FSE_USER_KEY=""
FSEGROUP1=""  # Primary FBO Group Access Key
FSEGROUP2=""  # Secondary/Aircraft Group Access Key

# Discord Webhooks
FBOHOOK="https://discord.com/api/webhooks/YOUR/FBO/HOOK"
MXHOOK="https://discord.com/api/webhooks/YOUR/MX/HOOK"

# Transfer Accounts (Numerical FSE Account IDs)
PERSONAL_ACC_ID=""       # Numerical Personal Account ID
AIRCRAFT_ACC_ID=""       # Numerical Aircraft Group ID
AIRCRAFT_ACC_NAME=""     # Display name for Aircraft Group
MAINT_ACC_ID=""          # Numerical Maintenance Group ID
MAINT_ACC_NAME=""        # Display name for Maintenance Group

# Financial Settings
MONTHLY_BUFFER=10000.00  # Must be in xxx.xx format with two decimals

# Overrides & Aircraft Configuration (Python Dictionary Syntax formatted as String)
AIRCRAFT="{'A62-001':700, 'VH-NUO':1000, 'VH-FCZ':115}"
FBO_OVERRIDES="{'YBMA': {'jet': '40ft', 'avgas': '20ft'}}"

API keys can be generated on the [FSEconomy Datafeeds page](https://server.fseconomy.net/datafeeds.jsp).


## Docker Compose Example

```yaml
services:
  fse_bot:
    build: .
    container_name: fse-fbo-bot
    restart: unless-stopped
    env_file:
      - .env
```

## Changelog

### [3.0.0] - 2026-10-02

#### Added
- Pre-flight API key validation using FSE XML endpoints to check User Key and Group Keys before running schedules.
- Aggregated error reporting on startup to log all invalid keys simultaneously.
- Automated monthly FBO operations reporting and fund transfers.
- Detailed descriptions and breakdown metrics in monthly aircraft reports.

#### Changed
- Refactored codebase into dedicated modules (`fse_api.py`, `analytics.py`, `config.py`).
- Updated API query handlers to check for XML `<Error>` tags prior to CSV parsing to prevent crashes on bad responses.
- Streamlined `requirements.txt` for production Docker deployments.

#### Fixed
- Process crashes caused by unhandled FSE API error responses returning malformed DataFrames.
- Container loop failures resulting from temporary DNS or network connection drops.

### [2.0.0] - 2024-08-14
- Combined FBO monitoring and monthly maintenance tracking scripts into a single application.
- Restructured application for Docker container deployment.

### [1.1.0]
- Switched notification delivery to direct Discord webhooks.

### [1.0.0]
- Initial release.