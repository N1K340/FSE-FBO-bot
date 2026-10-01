# fse_pipeline/reporters.py
from discord import Embed
import pandas as pd
from fse_pipeline.config import settings

def build_combined_fbo_embed(
    supplies_df: pd.DataFrame, 
    jeta_df: pd.DataFrame, 
    avgas_df: pd.DataFrame,
    test: bool = False
) -> Embed:
    """Compiles all FBO checks into a single clean, readable Discord embed."""
    title_prefix = "🧪 [TEST MODE] " if test else ""
    
    embed = Embed(
        title=f"{title_prefix}✈️ FSE FBO Daily Report",
        color=0x3498DB # Blue
    )

    # 1. Supplies Field
    if supplies_df.empty:
        embed.add_field(name="⚠️ Low Supplies Warning", value="✅ All airports have healthy supplies.", inline=False)
    else:
        lines = []
        for _, row in supplies_df.iterrows():
            lines.append(f"• **{row['Airport']}**: {row['SuppliedDays']} days remaining")
        embed.add_field(name="⚠️ Low Supplies Warning", value="\n".join(lines), inline=False)

    # 2. Jet-A Field
    if not jeta_df.empty:
        lines = []
        for _, row in jeta_df.iterrows():
            lines.append(f"• **{row['Airport']}**: {row['FuelJetA']:,.0f} kg remaining")
        embed.add_field(name="⛽ Jet-A Orders Needed", value="\n".join(lines), inline=False)

    # 3. Avgas Field
    if not avgas_df.empty:
        lines = []
        for _, row in avgas_df.iterrows():
            lines.append(f"• **{row['Airport']}**: {row['Fuel100LL']:,.0f} kg remaining")
        embed.add_field(name="⛽ Avgas Orders Needed", value="\n".join(lines), inline=False)

    return embed

def build_monthly_mx_embed(
    aircraft_summary: list[dict],
    month: str,
    year: str,
    monthly_aircraft_cost: float = 0.0,
    buffer_cost: float = 0.0,
    account_b_balance: float = 0.0,
    transfer_status: str = "Success",
    transfer_notes: str = "",
    test: bool = False
) -> Embed:
    """Builds a rich Discord embed detailing monthly lease usage, obligations, and cash transfers."""
    total_lease_cost = sum(item["cost"] for item in aircraft_summary)
    total_obligations = total_lease_cost + monthly_aircraft_cost + buffer_cost

    color = 0x2ECC71 if transfer_status == "Success" else 0xE74C3C  # Green or Red
    title_prefix = "🧪 [TEST MODE] " if test else ""

    embed = Embed(
        title=f"{title_prefix}📋 Monthly Aircraft Lease & Financial Report ({month}/{year})",
        color=color
    )

    if not aircraft_summary:
        embed.description = "No aircraft active or logged for this period."
    else:
        lines = [
            f"• **{item['rego']}**: {item['hours']} hrs @ ${item['rate']}/hr = **${item['cost']:,.2f}**"
            for item in aircraft_summary
        ]
        embed.add_field(name="Step 1: Aircraft Usage Lease Costs", value="\n".join(lines), inline=False)

    obligations_text = (
        f"• **Usage Lease Costs**: ${total_lease_cost:,.2f}\n"
        f"• **Aircraft Monthly Fees**: ${monthly_aircraft_cost:,.2f}\n"
        f"• **Buffer Amount**: ${buffer_cost:,.2f}\n"
        f"• **Total Required Obligations**: **${total_obligations:,.2f}**"
    )
    embed.add_field(name="Step 2: Monthly Financial Obligations", value=obligations_text, inline=False)

    status_symbol = "✅" if transfer_status == "Success" else "❌"
    transfer_text = (
        f"• **Account B Cash Balance**: ${account_b_balance:,.2f}\n"
        f"• **Transfer Status**: {status_symbol} {transfer_status}\n"
    )
    if transfer_notes:
        transfer_text += f"• **Details**: {transfer_notes}"

    embed.add_field(name="Step 3: Account Balance & Transfer Status", value=transfer_text, inline=False)

    return embed