import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta, timezone
import os

# -----------------------------
# CONFIGURATION BOT
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Fuseau horaire Paris
# -----------------------------
PARIS_TZ = timezone(timedelta(hours=1))  # UTC+1

# -----------------------------
# Stockage des timers
# -----------------------------
archi_timers = {}  # {"nom_archi": {"kill_time": datetime, "user": "pseudo"}}

# -----------------------------
# Archis avec ALERTE ROUGE
# -----------------------------
ALERTE_ROUGE = {
    "faufoll", "bulgig", "pioulette", "drakolage", "crognan",
    "ouature", "citassate", "serpistol", "fanburn", "fansis",
    "bistou", "abrinos", "bandapar"
}

# -----------------------------
# COMMANDES
# -----------------------------

@bot.command()
async def archi(ctx, *, nom_archi):
    """Enregistre un archimonstre tué"""
    now = datetime.now(PARIS_TZ)
    debut_repop = now + timedelta(hours=10)
    fin_repop = now + timedelta(hours=14)

    archi_timers[nom_archi.lower()] = {"kill_time": now, "user": ctx.author.name}

    # Message de confirmation
    await ctx.send(
        f"📝 **{nom_archi} enregistré !**\n"
        f"🟢 Début repop : {debut_repop.strftime('%H:%M')}\n"
        f"🔴 Fin repop : {fin_repop.strftime('%H:%M')}"
    )

    # ALERTE ROUGE si archi dans la liste spéciale
    if nom_archi.lower() in ALERTE_ROUGE:
        await ctx.send(
            f"🚨🚨🚨 **ALERTE ROUGE À TOUS LES CHASSEURS !** 🚨🚨🚨\n"
            f"⚔️ {nom_archi.title()} a été capturé ! Préparez-vous pour le repop !"
        )

    # Attente 30 minutes avant repop pour alerte
    delta_alerte = (debut_repop - timedelta(minutes=30)) - now
    await asyncio.sleep(max(delta_alerte.total_seconds(), 0))

    await ctx.send(
        f"⏰ **Alerte 30 minutes avant repop de {nom_archi} !**\n"
        f"🟢 Début repop prévu : {debut_repop.strftime('%H:%M')}"
    )

    # Attente jusqu'au début repop
    delta_debut = (debut_repop - now).total_seconds()
    await asyncio.sleep(max(delta_debut, 0))

    await ctx.send(
        f"🚨 **Début du repop de {nom_archi} !**\n"
        f"⏳ Jusqu'à {fin_repop.strftime('%H:%M')}"
    )

@bot.command()
async def repop(ctx):
    """Affiche les archis actuellement en repop"""
    now = datetime.now(PARIS_TZ)
    msg = "📋 **Archimonstres en repop :**\n"
    found = False
    for nom, data in archi_timers.items():
        debut = data["kill_time"] + timedelta(hours=10)
        fin = data["kill_time"] + timedelta(hours=14)
        if debut <= now <= fin:
            msg += f"- {nom.title()} (capturé par {data['user']}) : {debut.strftime('%H:%M')} – {fin.strftime('%H:%M')}\n"
            found = True
    if not found:
        msg += "Aucun archimonstre en repop actuellement."
    await ctx.send(msg)

@bot.command()
async def timer(ctx, *, nom_archi):
    """Montre le timer connu d’un archimonstre"""
    now = datetime.now(PARIS_TZ)
    data = archi_timers.get(nom_archi.lower())
    if data and now - data["kill_time"] <= timedelta(hours=24):
        debut = data["kill_time"] + timedelta(hours=10)
        fin = data["kill_time"] + timedelta(hours=14)
        await ctx.send(
            f"⏱️ **Timer connu !**\n"
            f"- Capturé par : {data['user']}\n"
            f"- Prochain repop : {debut.strftime('%H:%M')} – {fin.strftime('%H:%M')}"
        )
    else:
        await ctx.send(f"❌ Timer inconnu pour {nom_archi}")

@bot.command()
async def deletearchi(ctx, *, nom_archi):
    """Supprime un timer enregistré par erreur"""
    nom_key = nom_archi.lower()
    if nom_key in archi_timers:
        del archi_timers[nom_key]
        await ctx.send(f"❌ Timer de **{nom_archi}** supprimé avec succès.")
    else:
        await ctx.send(f"⚠️ Aucun timer trouvé pour **{nom_archi}**.")

@bot.command(name="archihelp")
async def archi_help(ctx):
    """Affiche la liste des commandes du bot archimonstre"""
    msg = (
        "📖 **Commandes du bot Archimonstre :**\n"
        "• `!archi <nom>` : Enregistre un archimonstre tué et programme les alertes.\n"
        "• `!timer <nom>` : Vérifie le dernier kill et le prochain repop si connu.\n"
        "• `!repop` : Affiche tous les archimonstres actuellement en repop.\n"
        "• `!deletearchi <nom>` : Supprime un timer enregistré par erreur.\n"
        "• `!archihelp` : Affiche cette aide."
    )
    await ctx.send(msg)

# -----------------------------
# TEST MESSAGES (optionnel)
# -----------------------------
@bot.event
async def on_message(message):
    print(f"Message reçu : {message.content}")
    await bot.process_commands(message)

# -----------------------------
# LANCEMENT DU BOT
# -----------------------------
bot.run(os.environ['DISCORD_TOKEN'])