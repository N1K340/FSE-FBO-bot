# fse_pipeline/notifications.py
from discord import SyncWebhook, Embed
from fse_pipeline.config import settings

def send_fbo_embed(embed: Embed):
    """Delivers the constructed embed to the FBO Discord channel."""
    webhook = SyncWebhook.from_url(settings.fbohook_url)
    webhook.send(embed=embed)

def send_mx_embed(embed: Embed):
    """Delivers the constructed embed to the Mainteancne Discord channel."""
    webhook = SyncWebhook.from_url(settings.mxhook_url)
    webhook.send(embed=embed)