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
    "faufoll","bulgig","pioulette","drakolage","crognan",
    "ouature","citassate","serpistol","fanburn","fansis",
    "bistou","abrinos","bandapar","roy","bistoulerieur",
    "bistoulequeteur","arabord","farlon","kannibal","léopolnor",
    "pandive","pekeutar","radoutable","yokaikoral","boostif"
}

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None,
                   activity=discord.Game(name="Joue à Dofus Retro – Ligue d’Otomai"))

# ================== DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"archis": {}, "daily": {}, "weekly": {}, "captures": []}, f, indent=2, ensure_ascii=False)
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
    try:
        nom = nom.lower().strip()
        t = now()
        start, end = repop_window(t)

        # Enregistrement
        uid = str(ctx.author.id)
        day = today_key()
        data["daily"].setdefault(day, {})
        points = 5 if nom in RARES else 1
        data["daily"][day][uid] = data["daily"][day].get(uid, 0) + points
        data["weekly"][uid] = data["weekly"].get(uid, 0) + points
        data["archis"][nom] = {"capture": t.isoformat(), "by": ctx.author.display_name}
        data.setdefault("captures", []).append({"nom": nom, "timestamp": t.isoformat()})
        save_data()

        # Message original
        msg = f"✅ {nom} enregistré par {ctx.author.display_name}\n🕒 Capturé à {fmt(t)}\n🔁 Repop entre {fmt(start)} et {fmt(end)}"
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
    except Exception as e:
        print(f"[ERROR] !archi : {e}")

@bot.command()
async def archipasmoi(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send(f"❌ Timer de {nom} inconnu.")
        return
    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)
    await ctx.send(
        f"ℹ️ {nom} déjà signalé par un autre chasseur\n🕒 Capturé à {fmt(cap)}\n🔁 Repop entre {fmt(start)} et {fmt(end)}\n⚠ Aucun point attribué."
    )

@bot.command()
async def timer(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send(f"❌ Timer de {nom} inconnu.")
        return
    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)
    await ctx.send(
        f"⏱️ **Timer de {nom} connu**\n🕒 Dernière capture à {fmt(cap)}\n🔁 Repop entre {fmt(start)} et {fmt(end)}"
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
async def prochainrepop(ctx):
    now_dt = now()
    end_window = now_dt + timedelta(hours=2)
    messages = []
    for cap in data.get("captures", []):
        cap_time = datetime.fromisoformat(cap["timestamp"])
        start, _ = repop_window(cap_time)
        if now_dt <= start <= end_window:
            messages.append(f"🌀 {cap['nom']} commencera sa phase de repop à {fmt(start)}")
    if not messages:
        await ctx.send("⏳ Aucun archimonstre n'entre en repop dans les 2 prochaines heures.")
        return
    await ctx.send("⏳ **Archimonstres entrant en repop :**\n" + "\n".join(messages))

@bot.command()
async def classement(ctx):
    classement_list = sorted(data["weekly"].items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 **Classement – Ligue d’Otomai**\n\n"
    for i, (uid, pts) in enumerate(classement_list[:10], 1):
        member = ctx.guild.get_member(int(uid))
        if member:
            total_archis = len([a for a in data["archis"] if a in data["archis"] and data["archis"][a]["by"] == member.display_name])
            rares_count = len([a for a in data["archis"] if a in RARES and data["archis"][a]["by"] == member.display_name])
            msg += f"{i}. {member.display_name} — {pts} pts ({total_archis} archis différents | {rares_count} rares)\n"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def resettimer(ctx):
    data["captures"] = []
    save_data()
    await ctx.send("⚡ Tous les timers des archis ont été réinitialisés par l’équipe administrative.")

@bot.command()
@commands.has_permissions(administrator=True)
async def resetweekly(ctx):
    role = discord.utils.get(ctx.guild.roles, name=MAITRE_ROLE_NAME)
    if not role or not data["weekly"]:
        await ctx.send("❌ Rôle ou points introuvables.")
        return
    winner_id = max(data["weekly"], key=data["weekly"].get)
    member = ctx.guild.get_member(int(winner_id))
    if not member:
        await ctx.send("❌ Gagnant introuvable.")
        return
    for m in ctx.guild.members:
        if role in m.roles:
            await m.remove_roles(role)
    await member.add_roles(role)
    await ctx.send(
        f"⚡️ Le Monde des Douze tremble devant cet exploit !\n"
        f"👑 {member.display_name} s’élève en Maître de la Ligue d’Otomai !\n"
        "💥 Les points hebdomadaires sont réinitialisés !\n"
        "❓ Qui sera le prochain Maître de la Ligue ?"
    )
    data["weekly"] = {}
    save_data()

# ================== TASKS ==================
@tasks.loop(minutes=60)
async def hourly_repop():
    t = now()
    for cap in data.get("captures", []):
        cap_time = datetime.fromisoformat(cap["timestamp"])
        start, end = repop_window(cap_time)
        if start <= t <= start + timedelta(minutes=1):
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    try:
                        if cap["nom"] in RARES:
                            await channel.send(f"🚨 **MONSTRE LÉGENDAIRE EN APPROCHE !** 🚨\n**{cap['nom']}** arrive !")
                        else:
                            await channel.send(f"🔔 **{cap['nom']}** est en phase de repop !")
                        break
                    except:
                        continue
        if t > end:
            data["captures"].remove(cap)
            save_data()

@tasks.loop(time=time(21,0,tzinfo=TIMEZONE))
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
                        f"⚡️ Le Monde des Douze tremble devant cet exploit !\n"
                        f"👑 {member.display_name} s’élève en Maître de la Ligue d’Otomai !\n"
                        "💥 Les points hebdomadaires sont réinitialisés !\n"
                        "❓ Qui sera le prochain Maître de la Ligue ?"
                    )
                    break
                except:
                    continue
        data["weekly"] = {}
        save_data()

# ================== RUN BOT ==================
bot.run(TOKEN)