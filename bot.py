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

# ================= DATA =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"archis": {}, "weekly": {}, "stats": {}}
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

def split_message(msg, limit=2000):
    parts = []
    while len(msg) > limit:
        split_index = msg.rfind("\n", 0, limit)
        if split_index == -1:
            split_index = limit
        parts.append(msg[:split_index])
        msg = msg[split_index:]
    parts.append(msg)
    return parts

# ================= ARCHI =================
@bot.command()
async def archi(ctx, nom: str):
    nom = nom.lower()
    uid = str(ctx.author.id)
    t = now()

    if nom in data["archis"]:
        cap = datetime.fromisoformat(data["archis"][nom]["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        await ctx.send(f"⚠️ **{nom}** déjà capturé → {start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}")
        return

    start, end = repop_window(t)
    data["archis"][nom] = {"capture": t.isoformat(), "by": uid}

    points = 10 if nom in LEGENDAIRES else 5 if nom in RARES else 1

    data["weekly"].setdefault(uid, {"points": 0, "archis": []})
    data["weekly"][uid]["points"] += points
    if nom not in data["weekly"][uid]["archis"]:
        data["weekly"][uid]["archis"].append(nom)

    data["stats"].setdefault(uid, {
        "total_points": 0,
        "total_captures": 0,
        "archis_uniques": [],
        "rares": 0,
        "legendaires": 0,
        "weekly_points": 0,
        "daily_points": 0,
        "records": {"best_week": 0},
        "last_capture": ""
    })
    s = data["stats"][uid]
    s["total_points"] += points
    s["total_captures"] += 1
    s["weekly_points"] += points
    s["daily_points"] += points
    s["last_capture"] = t.isoformat()
    if nom not in s["archis_uniques"]:
        s["archis_uniques"].append(nom)
    if nom in RARES:
        s["rares"] += 1
    if nom in LEGENDAIRES:
        s["legendaires"] += 1

    capture_time = t.strftime('%Hh%M')
    if nom in LEGENDAIRES:
        msg = (
            f"🌟💎 **CAPTURE LÉGENDAIRE !** 💎🌟\n"
            f"✅ **{nom}** enregistré par **{ctx.author.display_name}**\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}\n\n"
            f"💎 Une énergie colossale se condense dans votre pierre d’âme…\n"
            f"⚡️ Le Monde des Douze tremble sous votre puissance !\n"
            f"🔥 Les étoiles elles-mêmes s’inclinent devant votre triomphe ! 💥"
        )
    elif nom in RARES:
        msg = (
            f"⭐ **ARCHIMONSTRE RARE CAPTURÉ !** ⭐\n"
            f"✅ **{nom}** enregistré par **{ctx.author.display_name}**\n"
            f"🕒 Capturé à {capture_time}\n"
            f"🔁 Repop entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}\n\n"
            f"Une aura inhabituelle émane de cette créature…\n"
            f"Les chasseurs expérimentés savent que ces spécimens sont particulièrement recherchés."
        )
    else:
        msg = f"✅ **{nom}** enregistré | repop entre {start.strftime('%Hh%M')} et {end.strftime('%Hh%M')}"
    await ctx.send(msg)
    save_data()

# ================= TIMER INDIVIDUEL =================
@bot.command()
async def timer(ctx, nom: str):
    nom = nom.lower()
    t = now()
    if nom not in data["archis"]:
        await ctx.send(f"❌ Aucun timer trouvé pour **{nom}**")
        return

    info = data["archis"][nom]
    cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
    start, end = repop_window(cap)

    label = "💎" if nom in LEGENDAIRES else "⭐" if nom in RARES else ""
    if start <= t <= end:
        status = "🟢"
        timer_text = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}"
    elif t < start:
        status = "⏳"
        timer_text = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}"
    else:
        status = "🔴"
        timer_text = "Expiré"

    msg = f"{status} **{label} {nom}** → {timer_text}"
    await ctx.send(msg)

# ================= ARCHILIST =================
@bot.command()
async def archilist(ctx):
    t = now()
    msg = "📜 **Liste des archimonstres du jour** 📜\n\n"
    day_archis = [(nom, info) for nom, info in data["archis"].items() if datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE).date() == t.date()]
    for nom, info in sorted(day_archis, key=lambda x: datetime.fromisoformat(x[1]["capture"])):
        start, end = repop_window(datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE))
        status = "🔴" if t > end else "🟢"
        msg += f"{status} {nom} → {start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}\n"
    for part in split_message(msg):
        await ctx.send(part)

# ================= ARCHILISTME =================
@bot.command()
async def archilistme(ctx):
    t = now()
    uid = str(ctx.author.id)
    msg = f"📜 **Tes archimonstres du jour, {ctx.author.display_name}** 📜\n\n"
    day_archis = [(nom, info) for nom, info in data["archis"].items() if info["by"] == uid and datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE).date() == t.date()]
    for nom, info in sorted(day_archis, key=lambda x: datetime.fromisoformat(x[1]["capture"])):
        start, end = repop_window(datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE))
        status = "🔴" if t > end else "🟢"
        msg += f"{status} {nom} → {start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}\n"
    for part in split_message(msg):
        await ctx.send(part)

# ================= ARCHIPASMOI =================
@bot.command()
async def archipasmoi(ctx):
    t = now()
    uid = str(ctx.author.id)
    msg = f"📜 **Archimonstres non capturés aujourd'hui, {ctx.author.display_name}** 📜\n\n"
    
    # Archis capturés aujourd'hui par le joueur
    captured_today = {nom for nom, info in data["archis"].items()
                      if info["by"] == uid and datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE).date() == t.date()}
    
    # Tous archis connus
    all_archis = LEGENDAIRES | RARES | set(data["archis"].keys())  # Tous nom connus
    
    missing_archis = sorted(all_archis - captured_today)
    
    if not missing_archis:
        msg += "✅ Tu as capturé tous les archimonstres du jour !"
    else:
        for nom in missing_archis:
            info = data["archis"].get(nom)
            if info:
                cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
                start, end = repop_window(cap)
                timer_text = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}" if now() <= end else "Expiré"
            else:
                timer_text = "Non encore capturé"
            label = "💎" if nom in LEGENDAIRES else "⭐" if nom in RARES else ""
            msg += f"{label} {nom} → {timer_text}\n"
    
    for part in split_message(msg):
        await ctx.send(part)
# ================= CLASSEMENT =================
@bot.command()
async def classement(ctx):
    classement_sorted = sorted(
        data["weekly"].items(),
        key=lambda x: x[1]["points"],
        reverse=True
    )
    msg = "🏆 **Classement hebdomadaire** 🏆\n\n"
    for uid, info in classement_sorted:
        member = ctx.guild.get_member(int(uid))
        if not member:
            continue
        archis = set(info["archis"])
        rares = sum(1 for a in archis if a in RARES)
        leg = sum(1 for a in archis if a in LEGENDAIRES)
        msg += f"{member.display_name} - {info['points']} points ({len(archis)} archis, {rares} rares, {leg} légendaires)\n"
    await ctx.send(msg)

# ================= RESETWEEKLY =================
@bot.command()
@commands.has_permissions(administrator=True)
async def resetweekly(ctx):
    data["weekly"] = {}
    for uid in data["stats"]:
        data["stats"][uid]["weekly_points"] = 0
    save_data()
    await ctx.send("♻️ Classement hebdomadaire réinitialisé !")

# ================= MVP =================
@bot.command()
@commands.has_permissions(administrator=True)
async def mvp(ctx, pseudo: str):
    await ctx.send(f"🏅 **Champion d’Otomail : {pseudo} !** 🏅")

# ================= MYSTATS =================
@bot.command()
async def mystats(ctx):
    uid = str(ctx.author.id)
    s = data["stats"].get(uid)
    if not s:
        await ctx.send("❌ Aucune stat disponible.")
        return
    msg = (
        f"📊 **Tes stats, {ctx.author.display_name}** 📊\n"
        f"Points totaux : {s['total_points']}\n"
        f"Archis uniques : {len(s['archis_uniques'])}\n"
        f"Légendaires : {s['legendaires']}, Rares : {s['rares']}\n"
        f"Captures totales : {s['total_captures']}\n"
        f"Points cette semaine : {s['weekly_points']}\n"
        f"Points aujourd'hui : {s['daily_points']}"
    )
    await ctx.send(msg)

# ================= LOOP REPOP =================
@tasks.loop(minutes=1)
async def repop_loop():
    t = now()
    for nom, info in list(data["archis"].items()):
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)
        if t > end:
            del data["archis"][nom]
    save_data()

# ================= READY =================
@bot.event
async def on_ready():
    print("Bot prêt")
    print("Commandes disponibles :", [cmd.name for cmd in bot.commands])
    repop_loop.start()

bot.run(TOKEN)