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
MAITRE_ROLE_NAME = "Maître de la Ligue d’Otomaï"
ALERT_CHANNEL_NAME = "🤖⏰pokedex⌚🧌"

LEGENDAIRES = {
    "pioulette","drakolage","bandapar","ouature","crognan","bulgig"
}

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

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX,intents=intents,help_command=None)

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,"w",encoding="utf-8") as f:
            json.dump({"archis":{},"daily":{},"weekly":{}},f,indent=2)
    with open(DATA_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)

data = load_data()

def now():
    return datetime.now(TIMEZONE)

def fmt(t):
    return t.strftime("%Hh%M")

def repop_window(t):
    return t+timedelta(hours=10),t+timedelta(hours=14)

def today_key():
    return (now()-timedelta(minutes=1)).strftime("%Y-%m-%d")

@bot.event
async def on_ready():
    print("Bot prêt")
    hourly_repop.start()

@bot.command()
async def archi(ctx,nom:str):

    nom=nom.lower().strip()

    t=now()
    start,end=repop_window(t)

    uid=str(ctx.author.id)

    data["archis"][nom]={"capture":t.isoformat(),"by":uid}

    points=1
    if nom in RARES:
        points=5
    if nom in LEGENDAIRES:
        points=10

    day=today_key()

    data["daily"].setdefault(day,{})
    data["daily"][day][uid]=data["daily"][day].get(uid,0)+points

    data["weekly"][uid]=data["weekly"].get(uid,0)+points

    save_data()

    msg=f"✅ **{nom}** enregistré par {ctx.author.display_name}\n🕒 Capturé à {fmt(t)}\n🔁 Repop entre **{fmt(start)}** et **{fmt(end)}**"

    if nom in LEGENDAIRES:

        msg=(

        "🌟 **CAPTURE LÉGENDAIRE !** 🌟\n"
        f"{msg}\n\n"
        "💎 Une énergie colossale se condense dans votre pierre d’âme…\n"
        "⚡️ Le Monde des Douze tremble sous votre puissance !\n"
        "🔥 Les étoiles elles-mêmes s’inclinent devant votre triomphe ! 💥"

        )

    elif nom in RARES:

        msg=(

        "⭐ **ARCHIMONSTRE RARE CAPTURÉ !** ⭐\n"
        f"{msg}\n\n"
        "Une aura inhabituelle émane de cette créature…\n"
        "Les chasseurs expérimentés savent que ces spécimens sont particulièrement recherchés."

        )

    await ctx.send(msg)

@bot.command()
async def archilist(ctx):

    if not data["archis"]:
        await ctx.send("❌ Aucun archimonstre enregistré.")
        return

    msg="📜 **Liste des archimonstres actuellement enregistrés** 📜\n\n"

    for nom,info in data["archis"].items():

        cap=datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)
        start,end=repop_window(cap)

        msg+=f"🔹 **{nom}** — capturé à {fmt(cap)} | repop entre {fmt(start)} et {fmt(end)}\n"

    await ctx.send(msg)

@bot.command()
async def totalarchi(ctx):

    total=len(data["archis"])

    if total<10:
        txt="La chasse est calme aujourd’hui…"
    elif total<30:
        txt="La chasse commence à s’accélérer !"
    else:
        txt="🔥 La chasse est **INTENSE** !"

    await ctx.send(f"📊 **Total du jour – Guilde {ctx.guild.name}**\n🔢 {total} archimonstres différents capturés\n\n{txt}")

@bot.command()
async def classement(ctx):

    classement=sorted(data["weekly"].items(),key=lambda x:x[1],reverse=True)

    msg="🏆 **Classement – Ligue d’Otomaï**\n\n"

    for uid,points in classement:

        member=ctx.guild.get_member(int(uid))
        if not member:
            continue

        archis=set()
        rares=0
        leg=0

        for a,v in data["archis"].items():
            if v["by"]==uid:
                archis.add(a)
                if a in RARES:
                    rares+=1
                if a in LEGENDAIRES:
                    leg+=1

        msg+=f"{member.display_name} - {points} points ({len(archis)} archis différents, {rares} rares, {leg} légendaires)\n"

    await ctx.send(msg)

@tasks.loop(minutes=60)
async def hourly_repop():

    t=now()

    for nom,info in list(data["archis"].items()):

        cap=datetime.fromisoformat(info["capture"]).astimezone(TIMEZONE)

        start,end=repop_window(cap)

        if start<=t<=start+timedelta(minutes=1):

            await send_alert(nom)

        if t>end:

            del data["archis"][nom]
            save_data()

async def send_alert(nom):

    for guild in bot.guilds:

        channel=discord.utils.get(guild.text_channels,name=ALERT_CHANNEL_NAME)

        if not channel:
            return

        if nom in LEGENDAIRES:

            await channel.send(f"🚨 **MONSTRE LÉGENDAIRE EN APPROCHE !** 🚨\n**{nom}** arrive !")

        elif nom in RARES:

            await channel.send(f"⭐ **ARCHIMONSTRE RARE EN APPROCHE !** ⭐\n**{nom}** pourrait apparaître.")

        else:

            await channel.send(f"🔔 **{nom}** est en phase de repop !")

bot.run(TOKEN)