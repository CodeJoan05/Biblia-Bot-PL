import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

@client.tree.command(name="contact", description="Kontakt do autora bota")
async def contact(interaction: discord.Integration):
    embed = discord.Embed(
        title="Kontakt",
        description="Jeśli chcesz zgłosić błąd lub dać propozycję zmian w bocie skontaktuj się ze mną:\n\nDiscord: **code_joan**\nInstagram: **god.is.graceful**",
        color=12370112)
    await interaction.response.send_message(embed=embed)