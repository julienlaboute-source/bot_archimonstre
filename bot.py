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
MAITRE_ROLE_NAME = "Maître de la Ligue d’Otomaï"  # tréma sur I uniquement

# 🌟 LÉGENDAIRES (10 points)
LEGENDAIRES = {"pioulette", "drakolage", "bandapar", "ouature", "crognan", "bulgig"}

# ⭐ RARES (5 points)
RARES = {
    "faufoll", "citassate", "serpistol", "fanburn", "fansiss",
    "bistou", "abrinos",
    "roy", "bistoulerieur", "bistoulequeteur",
    "arabord", "arakule", "farlon", "kannibal", "léopolnor",
    "pandive", "pekeutar", "radoutable", "yokaikoral", "boostif",
    "bandson", "fanlmyl", "tiwoflan", "bi",
    "ribibi", "fantoch", "fanlabiz",
    "soryonara", "neufedur", "bombata", "sourizoto", "onihylis",
    "milipussien"
}

# ============================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
    activity=discord.Game(name="Joue à Dofus Retro – Ligue d’Otomaï")
)

# ================== DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE) or ".", exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"archis": {}, "daily": {}, "weekly": {}}, f, indent=2, ensure_ascii=False)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

# ================== UTILS ==================
def now():
    return datetime.now(TIMEZONE)

def fmt(dt):
    return dt.strftime("%Hh%M")

def repop_window(capture_time):
    start = capture_time + timedelta(hours=10)
    end = capture_time + timedelta(hours=14)
    return start, end

def today_key():
    return now().strftime("%Y-%m-%d")

# ================== EVENTS ==================
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user} – Version stable")
    hourly_repop.start()
    weekly_ligue.start()

# ================== COMMANDS ==================
@bot.command()
async def archi(ctx, nom: str):
    nom = nom.lower().strip()
    t = now()
    start, end = repop_window(t)

    # Enregistrement
    data["archis"][nom] = {"capture": t.isoformat(), "by": str(ctx.author.id)}
    uid = str(ctx.author.id)
    day = today_key()
    data["daily"].setdefault(day, {})
    points = 10 if nom in LEGENDAIRES else 5 if nom in RARES else 1
    data["daily"][day][uid] = data["daily"][day].get(uid, 0) + points
    data["weekly"][uid] = data["weekly"].get(uid, 0) + points
    save_data()

    # Message
    msg = f"✅ **{nom}** enregistré par {ctx.author.display_name}\n🕒 Capturé à {fmt(t)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"
    if nom in LEGENDAIRES:
        msg = (
            f"🌟 **CAPTURE LÉGENDAIRE !** 🌟\n"
            f"{msg}\n\n"
            "💎 Une énergie colossale se condense dans votre pierre d’âme…\n"
            "⚡️ Le Monde des Douze tremble sous votre puissance !\n"
            "🔥 Les étoiles elles-mêmes s’inclinent devant votre triomphe ! 💥"
        )
    await ctx.send(msg)
    try: await ctx.message.delete()
    except: pass

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
    points = 10 if nom in LEGENDAIRES else 5 if nom in RARES else 1
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
    classement = sorted(data["weekly"].items(), key=lambda x: x[1], reverse=True)
    msg = f"🏆 **Classement – Ligue d’Otomaï**\n\n"
    for i, (uid, count) in enumerate(classement[:10], 1):
        member = ctx.guild.get_member(int(uid))
        if member:
            archis_diff = sum(1 for a, info in data["archis"].items() if str(info.get("by")) == uid)
            rares_count = sum(1 for a, info in data["archis"].items() if str(info.get("by")) == uid and a in RARES)
            legend_count = sum(1 for a, info in data["archis"].items() if str(info.get("by")) == uid and a in LEGENDAIRES)
            msg += f"{i}. {member.display_name} — {count} points ({archis_diff} archis, {rares_count} rares, {legend_count} légendaires)\n"
    await ctx.send(msg)

@bot.command()
async def totalarchi(ctx):
    day = today_key()
    archis_today = {a for a, info in data["archis"].items() if datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE).strftime("%Y-%m-%d") == day}
    total = len(archis_today)
    if total < 10: txt = "La chasse est calme aujourd’hui…"
    elif total < 30: txt = "La chasse commence à s’accélérer !"
    else: txt = "🔥 La chasse est **INTENSE** !"
    await ctx.send(f"📊 **Total du jour – Guilde {ctx.guild.name}**\n🪨 {total} archimonstres différents capturés\n\n{txt}")

@bot.command()
async def archilist(ctx):
    if not data["archis"]:
        await ctx.send("Aucun archimonstre n’est enregistré pour le moment.")
        return
    msg = "**📜 Liste des archimonstres actuellement enregistrés :**\n\n"
    for nom, info in data["archis"].items():
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        msg += f"**{nom}** — Capturé à {fmt(cap)} — Repop entre {fmt(start)} et {fmt(end)}\n"
    await ctx.send(msg)

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
    if not found: msg += "Aucun archimonstre n’est en repop pour le moment."
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
    if not found: msg += "Aucun archimonstre ne repop dans les 2 prochaines heures."
    await ctx.send(msg)

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
        if not role: continue
        winner_id = max(data["weekly"], key=data["weekly"].get)
        member = guild.get_member(int(winner_id))
        if member:
            for m in guild.members:
                if role in m.roles: await m.remove_roles(role)
            await member.add_roles(role)
            # Envoi message dans le canal où la commande est exécutée
            try:
                await ctx.send(
                    f"🏆 **LIGUE D’OTOMAÏ** 🏆\n"
                    f"{member.display_name} devient **Maître de la Ligue** !\n\n"
                    "Concentration à toute épreuve, les dresseurs parcourent le Monde des Douze à toute allure "
                    "et font le plein de **pierres d’âmes** 🔥"
                )
            except: pass
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
        channel = discord.utils.get(guild.text_channels, name="🤖⏰pokedex⌚🧌")
        if channel:
            try:
                if nom in LEGENDAIRES:
                    await channel.send(
                        f"🚨 **MONSTRE LÉGENDAIRE EN APPROCHE !** 🚨\n"
                        f"**{nom}** arrive, préparez vos **pierres d’âmes** !\n"
                        "🌌 Une aura de puissance immense irradie la région… Le Monde des Douze retient son souffle !"
                    )
                else:
                    await channel.send(f"🔔 **{nom}** est en phase de repop !")
            except Exception as e:
                print(f"[ERROR] send_alert: {e}")

bot.run(TOKEN)