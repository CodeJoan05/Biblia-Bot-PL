import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

@client.tree.command(name="information", description="Informacje o bocie")
async def information(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Informacje",
        description="**Biblia** to bot, który umożliwia czytanie Biblii w wielu językach, co pozwala na dogłębne badanie różnic między tekstami oryginalnymi a ich tłumaczeniami.\n\nBot zawiera **18** przekładów Pisma Świętego w języku polskim, **3** w języku angielskim, **2** w języku niemieckim, **1** w języku łacińskim, **2** w języku greckim oraz **1** w języku hebrajskim.\n\n**Strona internetowa:** https://biblia-bot.netlify.app/\n\n[Terms of Service](https://biblia-bot.netlify.app/terms-of-service) | [Privacy Policy](https://biblia-bot.netlify.app/privacy-policy)",
        color=12370112)
    await interaction.response.send_message(embed=embed)