import discord, json, sqlite3
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

# Domyślne tłumaczenie

default_translations = {}

# Utworzenie bazy danych SQLite

conn = sqlite3.connect('data/user_settings.db')
c = conn.cursor()

# Tworzenie tabeli przechowującej ustawienia użytkowników

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT)''')

# Autouzupełnianie opcji w komendzie /setversion

async def translation_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    with open('resources/translations/bible_translations.txt', 'r') as file:
        bible_translations = [line.strip() for line in file]
    
    # Filtrowanie wersji Biblii na podstawie bieżących danych wejściowych
    return [
        app_commands.Choice(name=translation, value=translation)
        for translation in bible_translations
        if current.lower() in translation.lower()
    ][:25]  # Do 25 podpowiedzi

@client.tree.command(name="setversion", description="Ustawienie domyślnego przekładu Pisma Świętego")
@app_commands.autocomplete(translation=translation_autocomplete)
async def setversion(interaction: discord.Interaction, translation: str):
    await interaction.response.defer()

    with open('resources/translations/bible_translations.txt', 'r') as file:
        bible_translations = [line.strip() for line in file]

    if translation in bible_translations:
        default_translations[interaction.user.id] = translation

        # Zapisanie ustawień użytkownika do bazy danych
        c.execute("REPLACE INTO user_settings (user_id, default_translation) VALUES (?, ?)", (interaction.user.id, translation))
        conn.commit()
        
        with open('resources/translations/translations.json', 'r', encoding='utf-8') as f:
            translations = json.load(f)

        full_name = translations[translation]

        embed = discord.Embed(
            title="Ustawienie domyślnego przekładu Pisma Świętego",
            description=f'Twój domyślny przekład Pisma Świętego został ustawiony na: `{full_name}`',
            color=12370112)
        await interaction.followup.send(embed=embed)
    else:
        error_embed = discord.Embed(
            title="Błąd",
            description='Podano błędny przekład Pisma Świętego. Wszystkie skróty przekładów są dostępne w `/versions`',
            color=0xff1d15)
        await interaction.followup.send(embed=error_embed)