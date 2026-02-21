import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

# -----------------------------
# CONFIGURATION BOT
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# COMMANDES
# -----------------------------
@bot.command()
async def archi(ctx, *, nom_archi):
    kill_time = datetime.now()
    debut_repop = kill_time + timedelta(hours=10)
    fin_repop = kill_time + timedelta(hours=14)

    await ctx.send(
        f"📝 **{nom_archi} enregistré !**\n"
        f"🟢 Début repop : {debut_repop.strftime('%H:%M')}\n"
        f"🔴 Fin repop : {fin_repop.strftime('%H:%M')}"
    )

    # attente 10h avant alerte
    await asyncio.sleep(10 * 3600)

    await ctx.send(
        f"🚨 **Début du repop de {nom_archi} !**\n"
        f"⏳ Jusqu'à {fin_repop.strftime('%H:%M')}"
    )

# -----------------------------
# TEST MESSAGES (optionnel)
# -----------------------------
@bot.event
async def on_message(message):
    # Affiche tout ce que le bot voit dans le terminal
    print(f"Message reçu : {message.content}")
    await bot.process_commands(message)

# -----------------------------
# LANCEMENT DU BOT
# -----------------------------
bot.run(os.environ['DISCORD_TOKEN'])