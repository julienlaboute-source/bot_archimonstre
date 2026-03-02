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
    "roy", "bistoulerieur", "bistoulequeteur",
    "arabord", "farlon", "kannibal", "léopolnor",
    "pandive", "pekeutar", "radoutable", "yokaikoral", "boostif"
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
        print(f"[INFO] {DATA_FILE} introuvable, création d'un nouveau fichier.")
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

# ================== DEBUG ==================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print(f"[DEBUG] Message reçu : {message.content} de {message.author}")
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user} – Version stable")
    hourly_repop.start()

# ================== COMMANDES ==================
@bot.command()
async def archi(ctx, nom: str):
    nom = nom.lower().strip()
    t = now()
    start, end = repop_window(t)

    data["archis"][nom] = {"capture": t.isoformat(), "by": ctx.guild.name}
    uid = str(ctx.author.id)
    day = today_key()
    data["daily"].setdefault(day, {})
    points = 5 if nom in RARES else 1
    data["daily"][day][uid] = data["daily"][day].get(uid, 0) + points
    data["weekly"][uid] = data["weekly"].get(uid, 0) + points
    save_data()

    msg = f"✅ **{nom}** enregistré par {ctx.author.display_name}\n🕒 Capturé à {fmt(t)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"
    if nom in RARES:
        msg = (
            f"🌟 **CAPTURE LÉGENDAIRE !** 🌟\n"
            f"{msg}\n\n"
            "💎 Une énergie colossale se condense dans votre pierre d’âme… "
            "Le Monde des Douze tremble à la puissance de votre capture ! 💎"
        )
    await ctx.send(msg)
    try: await ctx.message.delete()
    except: pass

@bot.command()
async def archipasmoi(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        # On ajoute le timer mais sans points
        t = now()
        data["archis"][nom] = {"capture": t.isoformat(), "by": "autre"}
        save_data()
        await ctx.send(f"ℹ️ Timer de **{nom}** ajouté mais aucun point attribué.")
        return
    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)
    await ctx.send(f"ℹ️ **Timer de {nom} connu**\n🕒 Capturé à {fmt(cap)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**")

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
        "`!archipasmoi <nom>` — Transmettre un timer sans point\n"
        "`!timer <nom>` — Voir un timer\n"
        "`!deletearchi <nom>` — Supprimer un timer et retirer les points\n"
        "`!classement` — Classement hebdomadaire\n"
        "`!totalarchi` — Total du jour\n"
        "`!repop` — Archimonstres en repop\n"
        "`!prochainrepop` — Timer des prochains archis\n"
        "`!resetweekly` — Annonce le vainqueur et reset les points\n"
        "`!resettimer` — Reboot des timers (admins uniquement)"
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

@bot.command()
async def resetweekly(ctx):
    """Annonce le vainqueur et reset le classement hebdomadaire."""
    if not data["weekly"]:
        await ctx.send("⚠️ Aucun score enregistré cette semaine.")
        return

    winner_id = max(data["weekly"], key=data["weekly"].get)
    member = ctx.guild.get_member(int(winner_id))
    if not member:
        await ctx.send("⚠️ Impossible de retrouver le membre gagnant.")
        return

    role = discord.utils.get(ctx.guild.roles, name=MAITRE_ROLE_NAME)
    if role:
        for m in ctx.guild.members:
            if role in m.roles:
                await m.remove_roles(role)
        await member.add_roles(role)

    await ctx.send(
        f"🏆 **LIGUE D’OTOMAI** 🏆\n"
        f"Le monde des Douze tremble devant l'exploit de **{member.display_name}** !\n\n"
        "Concentration à toute épreuve, les dresseurs parcourent le Monde des Douze et font le plein de pierres d’âmes 🔥\n"
        "Qui sera le prochain Maître de la Ligue ? La bataille continue…"
    )

    data["weekly"] = {}
    save_data()

@bot.command()
@commands.has_permissions(administrator=True)
async def resettimer(ctx):
    """Reboot de tous les timers des archimonstres."""
    for nom in data["archis"]:
        data["archis"][nom]["capture"] = now().isoformat()
    save_data()
    await ctx.send("🔁 Tous les timers des archimonstres ont été réinitialisés !")

# ================== TASKS ==================
@tasks.loop(minutes=60)
async def hourly_repop():
    t = now()
    for nom, info in list(data["archis"].items()):
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if start <= t <= start + timedelta(minutes=1):
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    try:
                        if nom in RARES:
                            await channel.send(f"🚨 **MONSTRE LÉGENDAIRE EN APPROCHE !** 🚨\n**{nom}** arrive, préparez vos pierres d’âmes !")
                        else:
                            await channel.send(f"🔔 **{nom}** est en phase de repop !")
                        break
                    except: continue
        if t > end:
            del data["archis"][nom]
            save_data()

bot.run(TOKEN)