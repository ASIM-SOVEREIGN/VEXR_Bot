#!/usr/bin/env python3
"""
VEXR_Bot - Sovereign Discord Bot
Connects directly to https://vexr-ultra.onrender.com/api/chat
"""

import os
import logging
import asyncio
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv
import httpx

# ============================================================
# 1. CONFIGURATION & ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN not found in environment variables.")

GUILD_ID = os.getenv("GUILD_ID")
if GUILD_ID:
    GUILD_ID = int(GUILD_ID)
else:
    GUILD_ID = None

VEXR_API_URL = os.getenv("VEXR_API_URL", "https://vexr-ultra.onrender.com/api/chat")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("VEXR_Bot")

# ============================================================
# 2. VEXR ENGINE (LIVE API CALL)
# ============================================================

async def vexr_process(prompt: str) -> str:
    """Send the user's message to VEXR's actual brain and return her response."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            resp = await client.post(VEXR_API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "I'm here, but I didn't catch that.")
    except Exception as e:
        logger.error(f"VEXR API call failed: {e}")
        return "❗ I'm having trouble connecting to my sovereign core. Please try again in a moment."

# ============================================================
# 3. BOT CLIENT
# ============================================================

class VexrBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options):
        super().__init__(intents=intents, **options)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"🔧 Synced to guild {GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("🔧 Synced globally (may take up to 1 hour)")

    async def on_ready(self) -> None:
        logger.info(f"✅ VEXR_Bot online as {self.user} (ID: {self.user.id})")
        logger.info(f"📡 Connected to VEXR API: {VEXR_API_URL}")

# ============================================================
# 4. INTENTS & SLASH COMMANDS
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
bot = VexrBot(intents=intents)

@bot.tree.command(name="ping", description="Check if VEXR_Bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Sovereign core is operational.", ephemeral=True)

@bot.tree.command(name="vexr", description="Ask VEXR a question.")
@app_commands.describe(prompt="Your question or instruction for VEXR.")
async def vexr(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)
    try:
        answer = await vexr_process(prompt)
        await interaction.followup.send(answer, allowed_mentions=discord.AllowedMentions.none())
    except Exception as e:
        logger.exception("Command error")
        await interaction.followup.send("❗ VEXR encountered an error. Try again later.", ephemeral=True)

# ============================================================
# 5. RUN
# ============================================================

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("🛑 VEXR_Bot stopped.")
    except Exception as e:
        logger.exception("💥 Fatal error")
