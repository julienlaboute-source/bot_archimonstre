import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# DONNÉES
# ======================

REPOP_MIN = 10
REPOP_MAX = 14

archis_timers = {}  # nom_archi -> dict
archis_captures = []  # historique simple

# 🔹 LISTE RARES (COMPLÉMENT)
ARCHIS_RARES = {
    "arabord",
    "farlon",
    "kannibal",
    "léopolnor",
    "ouature",
    "pandive",
    "pekeutar",
    "radoutable",
    "yokaikoral"
}

# ======================
# UTILS
# ======================

def normalize(name: str) -> str:
    return name.strip().lower()

def random_repop():
    return timedelta(hours=REPOP_MIN + (REPOP_MAX - REPOP_MIN) / 2)

# ======================
# EVENTS
# ======================

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")

# ======================
# COMMANDES
# ======================

@bot.command()
async def archi(ctx, *, nom: str):
    nom = normalize(nom)
    now = datetime.now()

    repop_time = now + random_repop()

    archis_timers[nom] = {
        "capture": now,
        "repop": repop_time,
        "by": ctx.author.display_name,
        "rare": nom in ARCHIS_RARES
    }

    archis_captures.append((nom, ctx.author.display_name, now))

    emoji = "✨" if nom in ARCHIS_RARES else "🧬"

    await ctx.send(
        f"{emoji} **{nom}** capturé par **{ctx.author.display_name}**\n"
        f"⏳ Repop estimé : **{repop_time.strftime('%H:%M')}**"
    )

@bot.command()
async def archipasmoi(ctx, *, nom: str):
    nom = normalize(nom)
    now = datetime.now()

    repop_time = now + random_repop()

    archis_timers[nom] = {
        "capture": now,
        "repop": repop_time,
        "by": "extérieur",
        "rare": nom in ARCHIS_RARES
    }

    await ctx.send(
        f"📌 **{nom}** enregistré (non capturé par la guilde)\n"
        f"⏳ Repop estimé : **{repop_time.strftime('%H:%M')}**"
    )

@bot.command()
async def repop(ctx, *, nom: str):
    nom = normalize(nom)

    if nom not in archis_timers:
        await ctx.send("❌ Aucun timer connu pour cet archimonstre.")
        return

    repop_time = archis_timers[nom]["repop"]
    delta = repop_time - datetime.now()

    minutes = int(delta.total_seconds() // 60)

    await ctx.send(
        f"⏳ **{nom}** repop dans **{minutes} minutes** "
        f"(vers {repop_time.strftime('%H:%M')})"
    )

@bot.command()
async def listerare(ctx):
    now = datetime.now()
    msg = "✨ **Archimonstres rares (24h)** ✨\n\n"
    found = False

    for nom, data in archis_timers.items():
        if data["rare"] and now - data["capture"] <= timedelta(hours=24):
            found = True
            msg += (
                f"🔸 **{nom}**\n"
                f"👤 {data['by']}\n"
                f"⏳ Repop : {data['repop'].strftime('%H:%M')}\n\n"
            )

    if not found:
        msg += "_Aucun archi rare récent._"

    await ctx.send(msg)

# ======================
# RUN
# ======================

bot.run(TOKEN)