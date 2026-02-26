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

DATA_FILE = "/data/data.json"  # volume persistant Railway
MAITRE_ROLE_NAME = "Maître de la Ligue d’Otomai"

RARES = {
    "faufoll", "bulgig", "pioulette", "drakolage", "crognan",
    "ouature", "citassate", "serpistol", "fanburn", "fansis",
    "bistou", "abrinos", "bandapar",
    "roy", "bistoulerieur", "bistoulequeteur",
    "arabord", "farlon", "kannibal", "léopolnor",
    "pandive", "pekeutar", "radoutable", "yokaikoral"
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
    activity=discord.Game(name="Joue à Dofus Retro – Ligue d’Otomai")
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

# ================== DEBUG MESSAGES ==================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print(f"[DEBUG] Message reçu : {message.content} de {message.author}")
    await bot.process_commands(message)

# ================== EVENTS ==================
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user} – Version safe")
    hourly_repop.start()
    weekly_ligue.start()

# ================== COMMANDS ==================
@bot.command()
async def archi(ctx, nom: str):
    """Enregistre une capture d'archimonstre avec debug et message dramatique."""
    try:
        nom = nom.lower()
        t = now()
        start, end = repop_window(t)

        # Enregistrement
        data["archis"][nom] = {"capture": t.isoformat(), "by": ctx.guild.name}
        uid = str(ctx.author.id)
        day = today_key()
        data["daily"].setdefault(day, {})
        points = 5 if nom in RARES else 1
        data["daily"][day][uid] = data["daily"][day].get(uid, 0) + points
        data["weekly"][uid] = data["weekly"].get(uid, 0) + points
        save_data()

        # Construction du message
        msg = f"✅ **{nom}** enregistré\n🕒 Capturé à {fmt(t)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"

        if nom in RARES:
            msg = (
                f"🌟 **CAPTURE LÉGENDAIRE !** 🌟\n"
                f"{msg}\n\n"
                "💎 Une énergie colossale se condense dans votre pierre d’âme… "
                "Le Monde des Douze tremble à la puissance de votre capture ! 💎"
            )

        print(f"[DEBUG] Message construit pour {nom} : {msg}")
        await ctx.send(msg)

        # Optionnel : suppression du message utilisateur
        # await ctx.message.delete()

    except Exception as e:
        print(f"[ERROR] Erreur dans !archi : {e}")
        await ctx.send(f"❌ Une erreur est survenue lors de l'enregistrement de **{nom}**.")

@bot.command()
async def archipasmoi(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send(f"❌ Timer de **{nom}** inconnu.")
        return
    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)
    await ctx.send(f"ℹ️ **Timer de {nom} connu**\n🕒 Capturé à {fmt(cap)} par un autre chasseur\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**")

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
    await ctx.send(f"📊 **Total du jour – Guilde {ctx.guild.name}**\n🔢 {total} archimonstres capturés\n\n{txt}")

@bot.command()
async def archihelp(ctx):
    await ctx.send(
        "**📘 Commandes – Bot Archimonstre**\n"
        "`!archi <nom>` — Enregistrer une capture\n"
        "`!archipasmoi <nom>` — Transmettre un timer\n"
        "`!timer <nom>` — Voir un timer\n"
        "`!deletearchi <nom>` — Supprimer un timer et retirer les points\n"
        "`!classement` — Classement hebdomadaire\n"
        "`!totalarchi` — Total du jour\n"
        "`!repop` — Archimonstres en repop"
    )

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
                    await channel.send(f"🚨 **MONSTRE LÉGENDAIRE EN APPROCHE !** 🚨\n**{nom}** arrive, préparez vos **pierres d’âmes** !")
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
                        "Concentration à toute épreuve, les dresseurs parcourent le Monde des Douze à toute allure et font le plein de **pierres d’âmes** 🔥"
                    )
                    break
                except:
                    continue
        data["weekly"] = {}
        save_data()

bot.run(TOKEN)