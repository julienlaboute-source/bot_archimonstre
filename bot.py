import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import os
import json

TOKEN = os.environ["DISCORD_TOKEN"]
PREFIX = "!"
TIMEZONE = pytz.timezone("Europe/Paris")

DATA_FILE = "data.json"
ALERT_CHANNEL_NAME = "🤖⏰pokedex⌚🧌"

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

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ================== DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"archis": {}, "daily": {}, "weekly": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

def now():
    return datetime.now(TIMEZONE)

def repop_window(t):
    return t + timedelta(hours=10), t + timedelta(hours=14)

# ================== COMMANDES ==================
# ---- !archi ----
@bot.command()
async def archi(ctx, nom: str):
    nom = nom.lower()
    t = now()
    start, end = repop_window(t)
    uid = str(ctx.author.id)

    data["archis"][nom] = {"capture": t.isoformat(), "by": uid}

    points = 1
    if nom in RARES:
        points = 5
    if nom in LEGENDAIRES:
        points = 10

    data["weekly"].setdefault(uid, {"points": 0, "archis": []})
    data["weekly"][uid]["points"] += points
    if nom not in data["weekly"][uid]["archis"]:
        data["weekly"][uid]["archis"].append(nom)

    save_data()

    capture_time = t.strftime('%Hh%M')
    if nom in LEGENDAIRES:
        msg = (
            f"🌟💎 CAPTURE LÉGENDAIRE ! 💎🌟\n"
            f"✅ **{nom}** enregistré par {ctx.author.display_name}\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}\n\n"
            f"💎 Une énergie colossale se condense dans votre pierre d’âme…\n"
            f"⚡️ Le Monde des Douze tremble sous votre puissance !\n"
            f"🔥 Les étoiles elles-mêmes s’inclinent devant votre triomphe ! 💥"
        )
    elif nom in RARES:
        msg = (
            f"⭐ ARCHIMONSTRE RARE CAPTURÉ ! ⭐\n"
            f"✅ **{nom}** enregistré par {ctx.author.display_name}\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}\n\n"
            f"Une aura inhabituelle émane de cette créature…\n"
            f"Les chasseurs expérimentés savent que ces spécimens sont particulièrement recherchés."
        )
    else:
        msg = f"✅ **{nom}** enregistré par {ctx.author.display_name} | Repop {start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}"
    
    await ctx.send(msg)

# ---- !archipasmoi ----
@bot.command()
async def archipasmoi(ctx, nom: str):
    nom = nom.lower()
    t = now()
    start, end = repop_window(t)
    capture_time = t.strftime('%Hh%M')
    
    if nom in LEGENDAIRES:
        msg = (
            f"🌟💎 CAPTURE LÉGENDAIRE ! 💎🌟\n"
            f"✅ **{nom}** (timer affiché pour info)\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop estimé entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}\n\n"
            f"💎 Une énergie colossale se condense dans la pierre d’âme…\n"
            f"⚡️ Le Monde des Douze tremble sous votre puissance !\n"
            f"🔥 Les étoiles s’inclinent devant votre triomphe ! 💥\n"
            f"⚠️ Aucun point ne sera attribué avec cette commande"
        )
    elif nom in RARES:
        msg = (
            f"⭐ ARCHIMONSTRE RARE CAPTURÉ ! ⭐\n"
            f"✅ **{nom}** (timer affiché pour info)\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop estimé entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}\n\n"
            f"Une aura inhabituelle émane de cette créature…\n"
            f"⚠️ Aucun point ne sera attribué avec cette commande"
        )
    else:
        msg = f"✅ **{nom}** (timer affiché pour info) | Repop estimé {start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}\n⚠️ Aucun point ne sera attribué"
    
    await ctx.send(msg)

# ---- !archilist ----
@bot.command()
async def archilist(ctx):
    t = now()
    sorted_archis = sorted(data["archis"].items(), key=lambda x: x[1]["capture"])
    msgs = []
    temp_msg = ""
    for nom, info in sorted_archis:
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        timer = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}" if t <= end else "Expiré"
        line = f"{nom} → {timer}\n"
        if len(temp_msg) + len(line) > 1900:
            msgs.append(temp_msg)
            temp_msg = ""
        temp_msg += line
    if temp_msg:
        msgs.append(temp_msg)
    for m in msgs:
        await ctx.send(m)

# ---- !archilistme ----
@bot.command()
async def archilistme(ctx):
    t = now()
    uid = str(ctx.author.id)
    if uid not in data["weekly"]:
        await ctx.send("Tu n’as encore capturé aucun archimonstre aujourd’hui.")
        return
    sorted_archis = sorted(data["weekly"][uid]["archis"])
    msgs = []
    temp_msg = ""
    for nom in sorted_archis:
        if nom not in data["archis"]:
            timer = "Expiré"
        else:
            cap = datetime.fromisoformat(data["archis"][nom]["capture"]).astimezone(TIMEZONE)
            start, end = repop_window(cap)
            timer = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}" if t <= end else "Expiré"
        line = f"{nom} → {timer}\n"
        if len(temp_msg) + len(line) > 1900:
            msgs.append(temp_msg)
            temp_msg = ""
        temp_msg += line
    if temp_msg:
        msgs.append(temp_msg)
    for m in msgs:
        await ctx.send(m)

# ---- !timer <nom> ----
@bot.command()
async def timer(ctx, nom: str):
    nom = nom.lower()
    t = now()
    if nom not in data["archis"]:
        await ctx.send(f"❌ **{nom}** n’a pas été capturé aujourd’hui.")
        return
    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)
    if t < start:
        status = "⏳ Pas encore repop"
    elif start <= t <= end:
        status = "🟢 En repop"
    else:
        status = "🔴 Expiré"
    msg = f"{status} **{nom}**\n🕒 Capturé à {cap.strftime('%Hh%M')}\n🔁 Repop estimé entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}"
    await ctx.send(msg)

# ---- !repop ----
@bot.command()
async def repop(ctx):
    t = now()
    msgs = []
    temp_msg = ""
    for nom, info in data["archis"].items():
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if start <= t <= end:
            line = f"{nom} → En repop ({start.strftime('%Hh%M')} - {end.strftime('%Hh%M')})\n"
            if len(temp_msg) + len(line) > 1900:
                msgs.append(temp_msg)
                temp_msg = ""
            temp_msg += line
    if temp_msg:
        msgs.append(temp_msg)
    if not msgs:
        await ctx.send("Aucun archimonstre n'est actuellement en repop.")
        return
    for m in msgs:
        await ctx.send(m)

# ---- !prochainrepop ----
@bot.command()
async def prochainrepop(ctx):
    t = now()
    deux_heures = t + timedelta(hours=2)
    msgs = []
    temp_msg = ""
    for nom, info in data["archis"].items():
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if t < start <= deux_heures:
            line = f"{nom} → Prochain repop à {start.strftime('%Hh%M')} (jusqu'à {end.strftime('%Hh%M')})\n"
            if len(temp_msg) + len(line) > 1900:
                msgs.append(temp_msg)
                temp_msg = ""
            temp_msg += line
    if temp_msg:
        msgs.append(temp_msg)
    if not msgs:
        await ctx.send("Aucun archimonstre ne repop dans les 2 prochaines heures.")
        return
    for m in msgs:
        await ctx.send(m)

# ---- !classement ----
@bot.command()
async def classement(ctx):
    classement_sorted = sorted(data["weekly"].items(), key=lambda x: x[1]["points"], reverse=True)
    msg = "🏆 Classement 🏆\n\n"
    for uid, info in classement_sorted:
        member = ctx.guild.get_member(int(uid))
        if not member:
            continue
        archis = set(info["archis"])
        rares = sum(1 for a in archis if a in RARES)
        leg = sum(1 for a in archis if a in LEGENDAIRES)
        msg += f"{member.display_name} - {info['points']} points ({len(archis)} archis différents, {rares} rares, {leg} légendaires)\n"
    await ctx.send(msg)

# ---- !mystats ----
@bot.command()
async def mystats(ctx):
    uid = str(ctx.author.id)
    if uid not in data["weekly"]:
        await ctx.send("Aucune stat disponible.")
        return
    info = data["weekly"][uid]
    archis = set(info["archis"])
    rares = sum(1 for a in archis if a in RARES)
    leg = sum(1 for a in archis if a in LEGENDAIRES)
    msg = (
        f"📊 Stats de {ctx.author.display_name} 📊\n"
        f"Points : {info['points']}\n"
        f"Archis différents : {len(archis)}\n"
        f"Rares : {rares}\n"
        f"Légendaires : {leg}"
    )
    await ctx.send(msg)

# ================= COMMANDES ADMIN =================
@bot.command()
@commands.has_permissions(administrator=True)
async def resetweekly(ctx):
    for uid in data["weekly"]:
        data["weekly"][uid]["points"] = 0
        data["weekly"][uid]["archis"] = []
    save_data()
    await ctx.send("✅ Classement hebdomadaire réinitialisé.")

@bot.command()
@commands.has_permissions(administrator=True)
async def mvp(ctx, pseudo: str):
    await ctx.send(f"🏆 Champion d’Otomail : {pseudo} 🏆")

# ---- !deletetimer ----
@bot.command()
@commands.has_permissions(administrator=True)
async def deletetimer(ctx, nom: str):
    nom = nom.lower()
    if nom not in data["archis"]:
        await ctx.send(f"❌ **{nom}** n’est pas dans la liste des timers.")
        return
    uid = data["archis"][nom]["by"]
    points = 1
    if nom in RARES:
        points = 5
    if nom in LEGENDAIRES:
        points = 10
    if uid in data["weekly"]:
        data["weekly"][uid]["points"] -= points
        if nom in data["weekly"][uid]["archis"]:
            data["weekly"][uid]["archis"].remove(nom)
    del data["archis"][nom]
    save_data()
    await ctx.send(f"🗑️ **{nom}** supprimé du suivi et {points} points retirés du joueur.")

# ================= REPOP LOOP =================
@tasks.loop(minutes=60)
async def hourly_repop():
    t = now()
    for nom, info in list(data["archis"].items()):
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if start <= t <= start + timedelta(minutes=1):
            for guild in bot.guilds:
                channel = discord.utils.get(guild.text_channels, name=ALERT_CHANNEL_NAME)
                if channel:
                    await channel.send(f"🔔 **{nom}** est en repop !")
        if t > end:
            del data["archis"][nom]
    save_data()

@bot.event
async def on_ready():
    print("Bot prêt")
    hourly_repop.start()
    print("Commandes disponibles :", [c.name for c in bot.commands])

bot.run(TOKEN)