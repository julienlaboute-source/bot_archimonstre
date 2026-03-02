import discord
from discord.ext import commands
from datetime import datetime, timedelta
import pytz
import json
import os

# ⚠️ Récupération du token depuis la variable d'environnement DISCORD_TOKEN
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TIMEZONE = pytz.timezone("Europe/Paris")
MAITRE_ROLE_NAME = "Maître de la Ligue d'Otomaï"
DATA_FILE = "data.json"

RARES = {
    "faufoll", "bulgig", "pioulette", "drakolage", "crognan",
    "ouature", "citassate", "serpistol", "fanburn", "fansis",
    "bistou", "abrinos", "bandapar",
    "roy", "bistoulerieur", "bistoulequeteur",
    "farlon", "drageaufol", "kannibal", "kitsoufre",
    "pandive", "ribibi", "soryonara", "yokaikoral",
    "pekeutar", "arabord", "boostif"
}

# -----------------------
# DATA
# -----------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "scores": {},
            "weekly": {},
            "archis": {},
            "captures": []
        }
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# -----------------------
# READY
# -----------------------

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

# -----------------------
# ARCHI
# -----------------------

@bot.command()
async def archi(ctx, *, nom):
    try:
        user_id = str(ctx.author.id)
        nom = nom.lower()
        now = datetime.now(TIMEZONE)

        data["scores"].setdefault(user_id, 0)
        data["weekly"].setdefault(user_id, 0)
        data["archis"].setdefault(user_id, [])
        data.setdefault("captures", [])

        if nom not in data["archis"][user_id]:
            data["archis"][user_id].append(nom)

        data["scores"][user_id] += 1
        data["weekly"][user_id] += 1

        rare_bonus = ""
        if nom in RARES:
            data["scores"][user_id] += 1
            data["weekly"][user_id] += 1
            rare_bonus = "\n🌟 Archimonstre rare ! +1 point bonus"

        data["captures"].append({
            "nom": nom,
            "timestamp": now.isoformat()
        })

        save_data()

        await ctx.send(
            f"✅ {nom} enregistré par {ctx.author.display_name}\n"
            f"🕒 {now.strftime('%Hh%M')}"
            f"{rare_bonus}"
        )

    except Exception as e:
        print("ERREUR ARCHI:", e)
        await ctx.send("❌ Une erreur est survenue.")

# -----------------------
# ARCHIPASMOI
# -----------------------

@bot.command()
async def archipasmoi(ctx, *, nom):
    now = datetime.now(TIMEZONE)
    await ctx.send(
        f"👀 {nom.lower()} signalé par {ctx.author.display_name}\n"
        f"🕒 {now.strftime('%Hh%M')}\n"
        f"⚠ Aucun point attribué."
    )

# -----------------------
# TIMER PROCHAIN REPOP
# -----------------------

@bot.command()
async def timerprochain(ctx):
    now = datetime.now(TIMEZONE)
    window_end = now + timedelta(hours=2)

    data.setdefault("captures", [])

    messages = []

    for capture in data["captures"]:
        capture_time = datetime.fromisoformat(capture["timestamp"])
        repop_start = capture_time + timedelta(hours=2)

        if now <= repop_start <= window_end:
            messages.append(
                f"🌀 {capture['nom'].capitalize()} commencera sa phase de repop à {repop_start.strftime('%Hh%M')}."
            )

    if not messages:
        await ctx.send("⏳ Aucun archimonstre n'entre en phase de repop dans les 2 prochaines heures.")
        return

    await ctx.send(
        "⏳ **Archimonstres entrant en phase de repop :**\n\n"
        + "\n".join(messages)
    )

# -----------------------
# CLASSEMENT
# -----------------------

@bot.command()
async def classement(ctx):
    if not data["scores"]:
        await ctx.send("Aucun score enregistré.")
        return

    sorted_scores = sorted(
        data["scores"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    message = "🏆 **Classement Général** 🏆\n\n"

    for i, (user_id, score) in enumerate(sorted_scores[:10], 1):
        member = ctx.guild.get_member(int(user_id))
        if member:
            total_archis = len(data["archis"].get(user_id, []))
            rares_count = len([a for a in data["archis"].get(user_id, []) if a in RARES])

            message += (
                f"{i}. {member.display_name} — {score} pts "
                f"({total_archis} archis différents | {rares_count} rares)\n"
            )

    await ctx.send(message)

# -----------------------
# RESET WEEKLY (ADMIN ONLY)
# -----------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def resetweekly(ctx):
    try:
        if not data["weekly"]:
            await ctx.send("❌ Aucun point cette semaine.")
            return

        role = discord.utils.get(ctx.guild.roles, name=MAITRE_ROLE_NAME)

        winner_id = max(data["weekly"], key=data["weekly"].get)
        member = ctx.guild.get_member(int(winner_id))

        if role and member:
            for m in ctx.guild.members:
                if role in m.roles:
                    await m.remove_roles(role)

            await member.add_roles(role)

        await ctx.send(
            f"⚡️ Le Monde des Douze tremble devant cet exploit !\n"
            f"👑 {member.display_name} s’élève en Maître de la Ligue d'Otomaï !\n"
            f"💥 Les points hebdomadaires sont réinitialisés !\n"
            f"❓ Qui sera le prochain Maître de la Ligue ?"
        )

        data["weekly"] = {}
        save_data()

    except Exception as e:
        print("ERREUR RESET WEEKLY:", e)
        await ctx.send("❌ Une erreur est survenue.")

# -----------------------
# RESET TIMER (ADMIN ONLY)
# -----------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def resettimer(ctx):
    try:
        data["captures"] = []
        save_data()
        await ctx.send("⚡ Tous les timers des archis ont été réinitialisés par l’équipe administrative.")
    except Exception as e:
        print("ERREUR RESET TIMER:", e)
        await ctx.send("❌ Une erreur est survenue lors du reset des timers.")

# -----------------------

bot.run(TOKEN)