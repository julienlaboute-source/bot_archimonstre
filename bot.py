import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import os
import json

# ================== CONFIG ==================
TOKEN = os.environ["DISCORD_TOKEN"]
PREFIX = "!"
TIMEZONE = pytz.timezone("Europe/Paris")

DATA_FILE = "data.json"
MAITRE_ROLE_NAME = "Maître de la Ligue d’Otomaï"
ALERT_CHANNEL_NAME = "🤖⏰pokedex⌚🧌"

# ================== ARCHIS ==================
LEGENDAIRES = {"pioulette","drakolage","bandapar","ouature","crognan","bulgig"}
RARES = {
    "faufoll","fanburn","fansiss","fanlmyl","fanlabiz","fantoch",
    "bistou","bistoulerieur","bistoulequeteur",
    "abrinos","arabord","arakule","farlon",
    "kannibal","léopolnor","pandive","pekeutar",
    "radoutable","yokaikoral","boostif",
    "ribibi","soryonara","neufedur","bombata",
    "sourizoto","onihylis","milipussien","bi",
    "bandson","citassate","serpistol","tiwoflan"
}

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ================== DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"archis": {}, "daily": {}, "weekly": {}}, f, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ================== UTILS ==================
def now():
    return datetime.now(TIMEZONE)

def fmt(t):
    return t.strftime("%Hh%M")

def repop_window(t):
    return t + timedelta(hours=10), t + timedelta(hours=14)

def today_key():
    return (now() - timedelta(minutes=1)).strftime("%Y-%m-%d")

# ================== EVENTS ==================
@bot.event
async def on_ready():
    print("Bot prêt")
    hourly_repop.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print(f"[DEBUG] Message reçu : {message.content} de {message.author}")
    await bot.process_commands(message)

# ================== COMMANDES ==================
@bot.command()
async def archi(ctx, nom: str):
    nom = nom.lower().strip()
    t = now()
    start, end = repop_window(t)
    uid = str(ctx.author.id)

    data["archis"][nom] = {"capture": t.isoformat(), "by": uid}

    points = 1
    if nom in RARES:
        points = 5
    if nom in LEGENDAIRES:
        points = 10

    day = today_key()
    data["daily"].setdefault(day, {})
    data["daily"][day][uid] = data["daily"][day].get(uid, 0) + points
    data["weekly"][uid] = data["weekly"].get(uid, 0) + points

    save_data()

    msg = f"✅ **{nom}** enregistré par {ctx.author.display_name}\n🕒 Capturé à {fmt(t)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"

    if nom in LEGENDAIRES:
        msg = (
            "🌟💎 **CAPTURE LÉGENDAIRE !** 💎🌟\n"
            f"{msg}\n\n"
            "💎 Une énergie colossale se condense dans votre pierre d’âme…\n"
            "⚡️ Le Monde des Douze tremble sous votre puissance !\n"
            "🔥 Les étoiles elles-mêmes s’inclinent devant votre triomphe ! 💥"
        )
    elif nom in RARES:
        msg = (
            "⭐ **ARCHIMONSTRE RARE CAPTURÉ !** ⭐\n"
            f"{msg}\n\n"
            "Une aura inhabituelle émane de cette créature…\n"
            "Les chasseurs expérimentés savent que ces spécimens sont particulièrement recherchés."
        )

    await ctx.send(msg)
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command()
async def archipasmoi(ctx, nom: str):
    nom = nom.lower()
    t = now()
    start, end = repop_window(t)
    data["archis"][nom] = {"capture": t.isoformat(), "by": "unknown"}
    save_data()
    await ctx.send(f"ℹ️ **Timer ajouté pour {nom} sans point**\n🕒 Capturé à {fmt(t)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**")

@bot.command()
async def timer(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send(f"❌ Timer de **{nom}** inconnu.")
        return
    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)
    await ctx.send(f"⏱️ **Timer de {nom} connu**\n🕒 Dernière capture à {fmt(cap)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**")

@bot.command()
async def deletearchi(ctx, nom: str):
    nom = nom.lower()
    uid = str(ctx.author.id)
    day = today_key()
    points = 5 if nom in RARES else 1
    if nom in LEGENDAIRES:
        points = 10
    if nom in data["archis"]:
        del data["archis"][nom]
        if day in data["daily"] and uid in data["daily"][day]:
            data["daily"][day][uid] -= points
            if data["daily"][day][uid] <= 0:
                del data["daily"][day][uid]
        if uid in data["weekly"]:
            data["weekly"][uid] -= points
            if data["weekly"][uid] <= 0:
                del data["weekly"][uid]
        save_data()
        await ctx.send(f"🗑️ Timer de **{nom}** supprimé, points retirés.")
    else:
        await ctx.send("❌ Aucun timer trouvé.")

@bot.command()
async def classement(ctx):
    classement_sorted = sorted(data["weekly"].items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 **Classement – Ligue d’Otomaï**\n\n"
    for uid, points in classement_sorted:
        member = ctx.guild.get_member(int(uid))
        if not member:
            continue
        archis = set()
        rares = 0
        leg = 0
        for a, v in data["archis"].items():
            if v["by"] == uid:
                archis.add(a)
                if a in RARES:
                    rares += 1
                if a in LEGENDAIRES:
                    leg += 1
        msg += f"{member.display_name} - {points} points ({len(archis)} archis différents, {rares} rares, {leg} légendaires)\n"
    await ctx.send(msg)

@bot.command()
async def totalarchi(ctx):
    total = len(data["archis"])
    if total < 10:
        txt = "La chasse est calme aujourd’hui…"
    elif total < 30:
        txt = "La chasse commence à s’accélérer !"
    else:
        txt = "🔥 La chasse est **INTENSE** !"
    await ctx.send(f"📊 **Total du jour – Guilde {ctx.guild.name}**\n🔢 {total} archimonstres différents capturés\n\n{txt}")

@bot.command()
async def archilist(ctx):
    if not data["archis"]:
        await ctx.send("❌ Aucun archimonstre enregistré.")
        return

    msg = "📜 **Liste des archimonstres actuellement enregistrés** 📜\n\n"

    for nom, info in data["archis"].items():
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)

        if nom in LEGENDAIRES:
            line = f"🌟💎 **{nom.upper()}** 💎🌟 — capturé à {fmt(cap)} | repop entre {fmt(start)} et {fmt(end)}\n"
        elif nom in RARES:
            line = f"⭐ **{nom}** ⭐ — capturé à {fmt(cap)} | repop entre {fmt(start)} et {fmt(end)}\n"
        else:
            line = f"🔹 {nom} — capturé à {fmt(cap)} | repop entre {fmt(start)} et {fmt(end)}\n"

        msg += line

    await ctx.send(msg)

# ================== REPOP COMMANDS ==================
@bot.command()
async def repop(ctx):
    t = now()
    msg = "📢 **Archimonstres en repop actuellement** 📢\n\n"
    found = False
    for nom, info in data["archis"].items():
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if start <= t <= end:
            msg += f"🔔 **{nom}** — repop entre {fmt(start)} et {fmt(end)}\n"
            found = True
    if not found:
        msg += "Aucun archimonstre n’est en repop pour le moment."
    await ctx.send(msg)

@bot.command()
async def prochainrepop(ctx):
    t = now()
    msg = "📢 **Prochains archimonstres à repop** 📢\n\n"
    found = False
    for nom, info in data["archis"].items():
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if t <= start <= t + timedelta(hours=2):
            msg += f"🔔 **{nom}** — repop entre {fmt(start)} et {fmt(end)}\n"
            found = True
    if not found:
        msg += "Aucun archimonstre ne repop dans les 2 prochaines heures."
    await ctx.send(msg)

# ================== RESET ==================
@bot.command()
async def resettimer(ctx):
    data["archis"] = {}
    save_data()
    await ctx.send("🗑️ Tous les timers ont été réinitialisés.")

@bot.command()
async def resetweekly(ctx):
    if not data["weekly"]:
        await ctx.send("❌ Aucun score hebdomadaire à réinitialiser.")
        return
    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name=MAITRE_ROLE_NAME)
        if not role:
            continue
        winner_id = max(data["weekly"], key=data["weekly"].get)
        member = guild.get_member(int(winner_id))
        if member:
            for m in guild.members:
                if role in m.roles:
                    await m.remove_roles(role)
            await member.add_roles(role)
            for channel in guild.text_channels:
                try:
                    await channel.send(
                        f"🏆 **LIGUE D’OTOMAÏ** 🏆\n"
                        f"{member.display_name} devient **Maître de la Ligue** !\n\n"
                        "Concentration à toute épreuve, les dresseurs parcourent le Monde des Douze à toute allure "
                        "et font le plein de **pierres d’âmes** 🔥"
                    )
                    break
                except:
                    continue
    data["weekly"] = {}
    save_data()

# ================== TASKS ==================
@tasks.loop(minutes=60)
async def hourly_repop():
    t = now()
    for nom, info in list(data["archis"].items()):
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if start <= t <= start + timedelta(minutes=1):
            await send_alert(nom)
        if t > end:
            del data["archis"][nom]
            save_data()

async def send_alert(nom):
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=ALERT_CHANNEL_NAME)
        if not channel:
            return
        if nom in LEGENDAIRES:
            await channel.send(f"🌟💎 **MONSTRE LÉGENDAIRE EN APPROCHE !** 💎🌟\n**{nom}** arrive !")
        elif nom in RARES:
            await channel.send(f"⭐ **ARCHIMONSTRE RARE EN APPROCHE !** ⭐\n**{nom}** pourrait apparaître.")
        else:
            await channel.send(f"🔔 **{nom}** est en phase de repop !")

bot.run(TOKEN)