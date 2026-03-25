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

# ================= SPLIT =================
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

    # weekly
    data["weekly"].setdefault(uid, {"points": 0, "archis": []})
    data["weekly"][uid]["points"] += points
    if nom not in data["weekly"][uid]["archis"]:
        data["weekly"][uid]["archis"].append(nom)

    # stats permanentes
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

    save_data()
    await ctx.send(f"✅ **{nom}** → repop {start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}")

# ================= ARCHILIST =================
@bot.command()
async def archilist(ctx):
    t = now()
    today_start = t.replace(hour=0, minute=0, second=0, microsecond=0)

    archis = []
    for nom, info in data["archis"].items():
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        if cap >= today_start:
            start, end = repop_window(cap)
            archis.append((nom, start, end))

    archis.sort(key=lambda x: x[1])

    if not archis:
        await ctx.send("❌ Aucun archi aujourd’hui")
        return

    msg = "📜 Archis du jour :\n\n"
    for nom, start, end in archis:
        if start <= t <= end:
            status = "🟢"
            timer = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}"
        elif t < start:
            status = "⏳"
            timer = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}"
        else:
            status = "🔴"
            timer = "Expiré"

        msg += f"{status} **{nom}** → {timer}\n"

    for part in split_message(msg):
        await ctx.send(part)

# ================= ARCHILISTME =================
@bot.command()
async def archilistme(ctx):
    uid = str(ctx.author.id)
    t = now()
    today_start = t.replace(hour=0, minute=0, second=0, microsecond=0)

    archis = []
    for nom, info in data["archis"].items():
        if info["by"] != uid:
            continue
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        if cap >= today_start:
            start, end = repop_window(cap)
            archis.append((nom, start, end))

    if not archis:
        await ctx.send("❌ Aucun archi pour toi aujourd’hui")
        return

    archis.sort(key=lambda x: x[1])

    msg = f"📜 Tes archis aujourd’hui :\n\n"
    for nom, start, end in archis:
        if start <= t <= end:
            status = "🟢"
            timer = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}"
        elif t < start:
            status = "⏳"
            timer = f"{start.strftime('%Hh%M')} - {end.strftime('%Hh%M')}"
        else:
            status = "🔴"
            timer = "Expiré"

        msg += f"{status} **{nom}** → {timer}\n"

    for part in split_message(msg):
        await ctx.send(part)

# ================= MYSTATS =================
@bot.command()
async def mystats(ctx):
    uid = str(ctx.author.id)

    if uid not in data["stats"]:
        await ctx.send("❌ Pas de stats")
        return

    s = data["stats"][uid]

    msg = (
        f"📊 Stats {ctx.author.display_name}\n\n"
        f"🏆 Total points : {s['total_points']}\n"
        f"📅 Semaine : {s['weekly_points']}\n"
        f"📆 Jour : {s['daily_points']}\n\n"
        f"🎯 Captures : {s['total_captures']}\n"
        f"✨ Uniques : {len(s['archis_uniques'])}\n"
        f"⭐ Rares : {s['rares']}\n"
        f"💎 Légendaires : {s['legendaires']}\n"
    )

    await ctx.send(msg)

# ================= MVP =================
@bot.command()
@commands.has_permissions(administrator=True)
async def mvp(ctx, member: discord.Member):
    uid = str(member.id)
    pts = data["weekly"].get(uid, {}).get("points", 0)

    await ctx.send(
        f"🏆 **CHAMPION D'OTOMAI** 🏆\n\n"
        f"👑 {member.mention} avec **{pts} points**\n"
        f"🔥 Domination totale cette semaine !"
    )

# ================= RESET =================
@bot.command()
@commands.has_permissions(administrator=True)
async def resetweekly(ctx):
    for uid, s in data["stats"].items():
        if s["weekly_points"] > s["records"]["best_week"]:
            s["records"]["best_week"] = s["weekly_points"]
        s["weekly_points"] = 0

    data["weekly"] = {}
    save_data()
    await ctx.send("♻️ Reset weekly OK")

# ================= LOOP =================
@tasks.loop(minutes=1)
async def repop_loop():
    t = now()

    for nom, info in list(data["archis"].items()):
        cap = datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start, end = repop_window(cap)

        if t > end:
            del data["archis"][nom]

    save_data()

@bot.event
async def on_ready():
    print("Bot prêt")
    repop_loop.start()

bot.run(TOKEN)