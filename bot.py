import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Pour récupérer le pseudo serveur

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

TOKEN = os.environ["DISCORD_TOKEN"]

DATA_FILE = "data.json"

# ---------- RARES / LEGENDAIRES ----------
RARES = [
    "faufoll","fanburn","fansiss","fanlmyl","fanlabiz","fantoch",
    "bistou","bistoulerieur","bistoulequeteur",
    "abrinos","arabord","arakule","farlon",
    "kannibal","léopolnor","pandive","pekeutar",
    "radoutable","yokaikoral","boostif",
    "ribibi","soryonara","neufedur","bombata",
    "sourizoto","onihylis","milipussien","bi",
    "bandson","citassate","serpistol","tiwoflan"
]

LEGENDAIRES = {"pioulette","drakolage","bandapar","ouature","crognan","bulgig"}

# ---------- LOAD / SAVE ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"archis": {}, "stats": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ---------- READY ----------
@bot.event
async def on_ready():
    print("Bot prêt")
    print("Commandes disponibles :", [cmd.name for cmd in bot.commands])

# ---------- UTILS ----------
def get_repop():
    """Repop calculé par rapport à l'heure de capture"""
    now = datetime.now()
    return now + timedelta(hours=10), now + timedelta(hours=14)

# ---------- ARCHI ----------
@bot.command()
async def archi(ctx, *, nom):
    nom = nom.lower()
    user = str(ctx.author)

    repop_min, repop_max = get_repop()
    capture_time = datetime.now().strftime("%Hh%M")

    # Attribution des points
    if nom in LEGENDAIRES:
        points = 10
    elif nom in RARES:
        points = 5
    else:
        points = 1

    data["archis"][nom] = {
        "user": user,
        "capture_time": datetime.now().isoformat(),
        "repop_min": repop_min.isoformat(),
        "repop_max": repop_max.isoformat(),
        "points": points
    }

    data["stats"].setdefault(user, {"points": 0})
    data["stats"][user]["points"] += points

    save_data(data)

    if nom in LEGENDAIRES:
        msg = (
            f"🌟💎 CAPTURE LÉGENDAIRE ! 💎🌟\n"
            f"✅ {nom} enregistré par {user}\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop entre {repop_min.strftime('%Hh%M')} et {repop_max.strftime('%Hh%M')}\n\n"
            f"💎 Une énergie colossale se condense dans votre pierre d’âme…\n"
            f"⚡️ Le Monde des Douze tremble sous votre puissance !\n"
            f"🔥 Les étoiles elles-mêmes s’inclinent devant votre triomphe ! 💥"
        )
    elif nom in RARES:
        msg = (
            f"⭐ ARCHIMONSTRE RARE CAPTURÉ ! ⭐\n"
            f"✅ {nom} enregistré par {user}\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop entre {repop_min.strftime('%Hh%M')} et {repop_max.strftime('%Hh%M')}\n\n"
            f"Une aura inhabituelle émane de cette créature…\n"
            f"Les chasseurs expérimentés savent que ces spécimens sont particulièrement recherchés."
        )
    else:
        msg = (
            f"✨ ARCHIMONSTRE CAPTURÉ\n"
            f"✅ {nom} enregistré par {user}\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop entre {repop_min.strftime('%Hh%M')} et {repop_max.strftime('%Hh%M')}"
        )

    await ctx.send(msg)

# ---------- ARCHIPASMOI ----------
@bot.command()
async def archipasmoi(ctx, *, nom):
    nom = nom.lower()
    repop_min, repop_max = get_repop()

    data["archis"][nom] = {
        "user": "autre",
        "capture_time": datetime.now().isoformat(),
        "repop_min": repop_min.isoformat(),
        "repop_max": repop_max.isoformat(),
        "points": 0
    }

    save_data(data)

    await ctx.send(
        f"🕒 **Timer ajouté** pour **{nom}**\n"
        f"🔁 Repop entre {repop_min.strftime('%Hh%M')} et {repop_max.strftime('%Hh%M')}\n"
        f"👤 Capturé par quelqu’un d’autre (aucun point attribué)"
    )

# ---------- TIMER ----------
@bot.command()
async def timer(ctx, *, nom):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send("❌ Timer non connu")
        return
    info = data["archis"][nom]
    repop_min = datetime.fromisoformat(info["repop_min"])
    repop_max = datetime.fromisoformat(info["repop_max"])
    await ctx.send(
        f"⏱️ **{nom}**\n"
        f"🔁 {repop_min.strftime('%Hh%M')} - {repop_max.strftime('%Hh%M')}"
    )

# ---------- DELETE TIMER ----------
@bot.command()
async def deletetimer(ctx, *, nom):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send("❌ Archi non trouvé")
        return
    info = data["archis"][nom]
    user = info["user"]
    if info["points"] > 0 and user in data["stats"]:
        data["stats"][user]["points"] -= info["points"]
    del data["archis"][nom]
    save_data(data)
    await ctx.send(f"🗑️ **{nom} supprimé** (points retirés si nécessaire)")

# ---------- ARCHILIST ----------
@bot.command()
async def archilist(ctx):
    if not data["archis"]:
        await ctx.send("❌ Aucun archi aujourd’hui")
        return
    sorted_archis = sorted(data["archis"].items(), key=lambda x: x[1]["repop_min"])
    msg = "📜 **ARCHIMONSTRES DU JOUR** 📜\n\n"
    for nom, info in sorted_archis:
        repop_min = datetime.fromisoformat(info["repop_min"])
        repop_max = datetime.fromisoformat(info["repop_max"])
        emoji = "💎" if nom in LEGENDAIRES else "⭐" if nom in RARES else "✨"
        msg += f"{emoji} **{nom}** → {repop_min.strftime('%Hh%M')} - {repop_max.strftime('%Hh%M')}\n"
    await ctx.send(msg)

# ---------- ARCHILISTME ----------
@bot.command()
async def archilistme(ctx):
    user = str(ctx.author)
    result = []
    for nom, info in data["archis"].items():
        if info["user"] == user:
            repop_min = datetime.fromisoformat(info["repop_min"])
            repop_max = datetime.fromisoformat(info["repop_max"])
            result.append((nom, repop_min, repop_max))
    if not result:
        await ctx.send("❌ Aucun archi pour toi aujourd’hui")
        return
    result.sort(key=lambda x: x[1])
    msg = "🧍 **TES ARCHIS** 🧍\n\n"
    for nom, rmin, rmax in result:
        emoji = "💎" if nom in LEGENDAIRES else "⭐" if nom in RARES else "✨"
        msg += f"{emoji} **{nom}** → {rmin.strftime('%Hh%M')} - {rmax.strftime('%Hh%M')}\n"
    await ctx.send(msg)

# ---------- REPOP ----------
@bot.command()
async def repop(ctx):
    now = datetime.now()
    en_cours = []
    bientot = []
    for nom, info in data["archis"].items():
        repop_min = datetime.fromisoformat(info["repop_min"])
        repop_max = datetime.fromisoformat(info["repop_max"])
        if repop_min <= now <= repop_max:
            en_cours.append(f"🟢 **{nom}** → {repop_min.strftime('%Hh%M')} - {repop_max.strftime('%Hh%M')}")
        elif now < repop_min and (repop_min - now).total_seconds() <= 7200:
            bientot.append(f"🟡 **{nom}** → {repop_min.strftime('%Hh%M')}")
    message = ""
    if en_cours:
        message += "**🟢 REPOP EN COURS :**\n" + "\n".join(en_cours) + "\n\n"
    if bientot:
        message += "**🟡 PROCHAINS REPOP (<2h) :**\n" + "\n".join(bientot)
    if not message:
        message = "❌ Aucun repop en cours ou prévu."
    await ctx.send(message)

# ---------- PROCHAIN REPOP ----------
@bot.command()
async def prochainrepop(ctx):
    now = datetime.now()
    bientot = []
    for nom, info in data["archis"].items():
        repop_min = datetime.fromisoformat(info["repop_min"])
        if now < repop_min and (repop_min - now).total_seconds() <= 7200:
            bientot.append(f"🟡 **{nom}** → {repop_min.strftime('%Hh%M')}")
    if not bientot:
        await ctx.send("❌ Aucun prochain repop dans les 2h")
    else:
        await ctx.send("**🟡 PROCHAINS REPOP (<2h) :**\n" + "\n".join(bientot))

# ---------- RESET TIMER ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def resettimer(ctx):
    for nom, info in list(data["archis"].items()):
        user = info["user"]
        if info["points"] > 0 and user in data["stats"]:
            data["stats"][user]["points"] -= info["points"]
        del data["archis"][nom]
    save_data(data)
    await ctx.send("♻️ Tous les timers ont été réinitialisés (points retirés si nécessaire)")

# ---------- RESET WEEKLY ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def resetweekly(ctx):
    data["stats"] = {}
    save_data(data)
    await ctx.send("♻️ Reset effectué")

# ---------- CLASSEMENT ----------
@bot.command()
async def classement(ctx):
    if not data["stats"]:
        await ctx.send("❌ Aucun classement")
        return

    guild = ctx.guild
    msg = "🏆 **CLASSEMENT DES CHASSEURS** 🏆\n\n"

    ranking = sorted(data["stats"].items(), key=lambda x: x[1]["points"], reverse=True)
    for user_id_str, stats in ranking:
        member = discord.utils.get(guild.members, name=user_id_str)  # pseudo serveur
        display_name = member.display_name if member else user_id_str

        archis_captures = [n for n, info in data["archis"].items() if info["user"] == user_id_str]
        total_archis = len(archis_captures)
        rares_count = sum(1 for n in archis_captures if n in RARES)
        legends_count = sum(1 for n in archis_captures if n in LEGENDAIRES)

        msg += f"**{display_name}** → {stats['points']} pts : {total_archis} archis différents ({rares_count} Rares, {legends_count} Légendaires)\n"

    await ctx.send(msg)

# ---------- MYSTATS ----------
@bot.command()
async def mystats(ctx):
    user = str(ctx.author)
    if user not in data["stats"]:
        await ctx.send("❌ Aucune stat")
        return

    pts = data["stats"][user]["points"]
    archis_captures = [n for n, info in data["archis"].items() if info["user"] == user]
    total_archis = len(archis_captures)
    rares_count = sum(1 for n in archis_captures if n in RARES)
    legends_count = sum(1 for n in archis_captures if n in LEGENDAIRES)

    await ctx.send(
        f"📊 **TES STATS** 📊\n\n👤 {user}\n"
        f"🏆 Points : {pts}\n"
        f"✨ Archis capturés : {total_archis}\n"
        f"⭐ Rares : {rares_count}\n"
        f"💎 Légendaires : {legends_count}"
    )

# ---------- MVP ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def mvp(ctx, pseudo):
    await ctx.send(f"🏆 MVP : {pseudo}")

bot.run(TOKEN)