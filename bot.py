import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, time
import pytz
import os
import json

# ================== CONFIG ==================
TOKEN = os.environ["DISCORD_TOKEN"]
PREFIX = "!"
TIMEZONE = pytz.timezone("Europe/Paris")

DATA_FILE = "data.json"
MAITRE_ROLE_NAME = "Maître de la Ligue d’Otomai"

RARES = {
    "faufoll", "bulgig", "pioulette", "drakolage", "crognan",
    "ouature", "citassate", "serpistol", "fanburn", "fansis",
    "bistou", "abrinos", "bandapar",
    "roy", "bistoulerieur", "bistoulequeteur"
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
    activity=discord.Game(name="Pokédex – Ligue d’Otomai")
)

# ================== DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"archis": {}, "daily": {}, "weekly": {}}
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
    print(f"Bot connecté : {bot.user}")
    hourly_repop.start()
    weekly_ligue.start()

# ================== COMMANDS ==================
@bot.command()
async def archi(ctx, nom: str):
    nom = nom.lower()
    t = now()
    start, end = repop_window(t)

    data["archis"][nom] = {
        "capture": t.isoformat(),
        "by": ctx.guild.name
    }

    uid = str(ctx.author.id)
    day = today_key()

    data["daily"].setdefault(day, {})
    data["daily"][day][uid] = data["daily"][day].get(uid, 0) + 1
    data["weekly"][uid] = data["weekly"].get(uid, 0) + 1

    save_data()
    await ctx.message.delete()

    legendary = nom in RARES

    msg = (
        f"✅ **{nom}** enregistré\n"
        f"🕒 Capturé à {fmt(t)}\n"
        f"🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"
    )

    if legendary:
        msg = (
            f"🌟 **CAPTURE LÉGENDAIRE !** 🌟\n"
            f"{msg}\n\n"
            "Félicitations dresseur, un monstre légendaire rejoint le Pokédex !"
        )

    await ctx.send(msg)

@bot.command()
async def archipasmoi(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send(f"❌ Timer de **{nom}** inconnu.")
        return

    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)

    await ctx.send(
        f"ℹ️ **Timer de {nom} connu**\n"
        f"🕒 Capturé à {fmt(cap)} par un autre chasseur\n"
        f"🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"
    )

@bot.command()
async def timer(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send(f"❌ Timer de **{nom}** inconnu.")
        return

    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)

    await ctx.send(
        f"⏱️ **Timer de {nom} connu**\n"
        f"🕒 Dernière capture à {fmt(cap)}\n"
        f"🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"
    )

@bot.command()
async def deletearchi(ctx, nom: str):
    nom = nom.lower()
    if nom in data["archis"]:
        del data["archis"][nom]
        save_data()
        await ctx.send(f"🗑️ Timer de **{nom}** supprimé.")
    else:
        await ctx.send("❌ Aucun timer trouvé.")

@bot.command()
async def classement(ctx):
    classement = sorted(data["weekly"].items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 **Classement – Ligue d’Otomai**\n\n"

    for i, (uid, count) in enumerate(classement[:10], 1):
        member = ctx.guild.get_member(int(uid))
        if member:
            msg += f"{i}. {member.display_name} — {count} archis\n"

    await ctx.send(msg)

@bot.command()
async def totalarchi(ctx):
    day = today_key()
    total = sum(data["daily"].get(day, {}).values())

    if total < 10:
        txt = "La chasse est calme aujourd’hui…"
    elif total < 30:
        txt = "La chasse commence à s’accélérer !"
    else:
        txt = "🔥 La chasse est **INTENSE** !"

    await ctx.send(
        f"📊 **Total du jour – Guilde {ctx.guild.name}**\n"
        f"🔢 {total} archimonstres capturés\n\n{txt}"
    )

@bot.command()
async def archihelp(ctx):
    await ctx.send(
        "**📘 Commandes – Bot Archimonstre**\n"
        "`!archi <nom>` — Enregistrer une capture\n"
        "`!archipasmoi <nom>` — Transmettre un timer\n"
        "`!timer <nom>` — Voir un timer\n"
        "`!deletearchi <nom>` — Supprimer un timer\n"
        "`!classement` — Classement hebdomadaire\n"
        "`!totalarchi` — Total du jour\n"
    )

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
        for channel in guild.text_channels:
            try:
                if nom in RARES:
                    await channel.send(
                        f"🚨 **MONSTRE LÉGENDAIRE EN APPROCHE !** 🚨\n"
                        f"Attention à tous les dresseurs,\n"
                        f"**{nom}** arrive, préparez vos **pierres d’âmes** !"
                    )
                else:
                    await channel.send(f"🔔 **{nom}** est en phase de repop !")
                return
            except:
                continue

@tasks.loop(time=time(21, 0, tzinfo=TIMEZONE))
async def weekly_ligue():
    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name=MAITRE_ROLE_NAME)

        if not role or not data["weekly"]:
            return

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
                        f"🏆 **LIGUE D’OTOMAI** 🏆\n"
                        f"{member.display_name} devient **Maître de la Ligue** !\n\n"
                        "Concentration à toute épreuve,\n"
                        "les dresseurs parcourent le Monde des Douze à toute allure\n"
                        "et font le plein de **pierres d’âmes** 🔥"
                    )
                    break
                except:
                    continue

        data["weekly"] = {}
        save_data()

bot.run(TOKEN)