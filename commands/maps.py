import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

@client.tree.command(name="maps", description="Mapy z Biblii")
@app_commands.describe(map="Wybierz mapę")
@app_commands.choices(map=[
    app_commands.Choice(name="Kraje podróży Abrahama", value="Kraje podróży Abrahama"),
    app_commands.Choice(name="Mapa plemion izraelskich", value="Mapa plemion izraelskich"),
    app_commands.Choice(name="Palestyna w czasach Nowego Testamentu", value="Palestyna w czasach Nowego Testamentu"),
    app_commands.Choice(name="Podróże Apostoła Pawła", value="Podróże Apostoła Pawła")
])

async def maps(interaction: discord.Interaction, map: app_commands.Choice[str]):

    file_path = f'resources/maps/{map.value}.jpg'

    try:
        image = discord.File(file_path, filename='map.jpg')

        embed = discord.Embed(
            title=map.name,
            color=12370112
        )

        embed.set_image(url="attachment://map.jpg")

        await interaction.response.send_message(embed=embed, file=image)
    
    except FileNotFoundError:
        error_embed = discord.Embed(
            title="Błąd",
            description="Mapa nie została znaleziona",
            color=0xff1d15
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)