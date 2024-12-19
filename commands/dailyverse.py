import discord, datetime, asyncio, pytz, json, sqlite3, os
from discord.ext import commands
from discord import app_commands
from typing import List
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

# Utworzenie bazy danych SQLite

conn = sqlite3.connect('data/user_settings.db')
c = conn.cursor()

# Tworzenie tabeli przechowującej ustawienia użytkowników

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT)''')

# Funkcja do tworzenia indeksu rozdziałów i wersetów na podstawie pliku danego przekładu Biblii

def create_bible_index(translation: str):
    bible_index = {}

    bible_path = f'resources/bibles/{translation}.json'
    if not os.path.exists(bible_path):
        return None

    with open(bible_path, 'r', encoding='utf-8') as file:
        bible_data = json.load(file)

    for verse in bible_data:
        book_name = verse['book_name']
        chapter = verse['chapter']
        verse_number = verse['verse']

        if book_name not in bible_index:
            bible_index[book_name] = {}

        if chapter not in bible_index[book_name]:
            bible_index[book_name][chapter] = []

        bible_index[book_name][chapter].append(verse_number)

    return bible_index

# Funkcja autouzupełniania dla nazw ksiąg

async def autocomplete_books(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice]:
    with open('resources/booknames/english_polish.json', 'r', encoding='utf-8') as file:
        english_to_polish_books = json.load(file)

    return [
        discord.app_commands.Choice(name=pl, value=pl)
        for pl in english_to_polish_books.values()
        if current.lower() in pl.lower()
    ][:15]  # Ograniczenie do 15 wyników

# Funkcja autouzupełniania dla rozdziałów

async def autocomplete_chapter(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice]:
    book = interaction.namespace.book
    user_id = interaction.user.id

    with open('resources/booknames/english_polish.json', 'r', encoding='utf-8') as file:
        english_to_polish_books = json.load(file)

    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()

    if not user_data:
        return []

    translation = user_data[1]

    bible_index = create_bible_index(translation)
    if not bible_index:
        return []

    # Znajduje angielską nazwę księgi
    english_book_name = None
    for en, pl in english_to_polish_books.items():
        if pl == book:
            english_book_name = en
            break

    if not english_book_name or english_book_name not in bible_index:
        return []

    # Pobiera dostępne rozdziały dla księgi
    chapters = list(bible_index[english_book_name].keys())

    return [
        discord.app_commands.Choice(name=str(chapter), value=str(chapter))
        for chapter in chapters if current.isdigit() and current in str(chapter)
    ][:15]  # Ograniczenie do 15 wyników

# Funkcja autouzupełniania dla wersetów

async def autocomplete_verse(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice]:
    book = interaction.namespace.book
    chapter = interaction.namespace.chapter
    user_id = interaction.user.id

    with open('resources/booknames/english_polish.json', 'r', encoding='utf-8') as file:
        english_to_polish_books = json.load(file)

    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()

    if not user_data:
        return []

    translation = user_data[1]

    bible_index = create_bible_index(translation)
    if not bible_index:
        return []

    # Znajduje angielską nazwę księgi
    english_book_name = None
    for en, pl in english_to_polish_books.items():
        if pl == book:
            english_book_name = en
            break

    if not english_book_name or english_book_name not in bible_index:
        return []

    # Pobiera dostępne wersety dla danego rozdziału
    verses = bible_index[english_book_name].get(int(chapter), [])

    return [
        discord.app_commands.Choice(name=str(verse), value=str(verse))
        for verse in verses if current.isdigit() and current in str(verse)
    ][:15]  # Ograniczenie do 15 wyników

# Komenda /dailyverse

@client.tree.command(name="dailyverse", description="Wyświetla werset dnia z Biblii")
@app_commands.autocomplete(book=autocomplete_books, chapter=autocomplete_chapter, start_verse=autocomplete_verse, end_verse=autocomplete_verse)
@app_commands.describe(book="Nazwa księgi", chapter="Numer rozdziału", start_verse="Numer wersetu początkowego", end_verse="Numer wersetu końcowego", hour="Godzina wysłania wiadomości (w formacie HH:MM)")
async def dailyverse(interaction: discord.Interaction, book: str, chapter: int, start_verse: int, end_verse: int, hour: str = None):
    await interaction.response.defer()
   
    user_id = interaction.user.id

    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
   
    if not user_data:
        embed = discord.Embed(
            title="Ustaw domyślny przekład Pisma Świętego",
            description='Aby korzystać z funkcji wyszukiwania fragmentów Biblii, musisz najpierw ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`. Aby ustawić domyślny przekład Pisma Świętego należy podać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`',
            color=12370112)
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    translation = user_data[1]

    with open(f'resources/bibles/{translation}.json', 'r') as file:
        bible = json.load(file)

    with open('resources/booknames/english_polish.json', 'r', encoding='utf-8') as file:
        english_to_polish_books = json.load(file)

    with open('resources/translations/translations.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)

    try:
        # Znajduje angielską nazwę księgi na podstawie polskiej nazwy
        english_book_name = None
        for en, pl in english_to_polish_books.items():
            if pl == book:
                english_book_name = en
                break

        if not english_book_name:
            error_embed = discord.Embed(
                title="Błąd",
                description="Nie znaleziono podanej nazwy księgi",
                color=0xff1d15
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Znajdowanie odpowiedniego wersetu
        selected_verses = [
            verse for verse in bible
            if verse['book_name'] == english_book_name and verse['chapter'] == chapter
            and start_verse <= verse['verse'] <= end_verse
        ]

        if not selected_verses:
            error_embed = discord.Embed(
                title="Błąd",
                description="Nie znaleziono podanego fragmentu",
                color=0xff1d15
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        title = f"{book} {chapter}:{start_verse}-{end_verse}"
        description = " ".join(
            f"**({verse['verse']})** {verse['text']}" for verse in selected_verses
        )

        embed = discord.Embed(title=title, description=description, color=12370112)
        embed.set_footer(text=f'{translations[translation]}')

        if hour:
            now = datetime.now(pytz.timezone('Europe/Warsaw'))
            send_time = datetime.strptime(hour, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            send_time = pytz.timezone('Europe/Warsaw').localize(send_time)

            if send_time < now:
                send_time += timedelta(days=1)

            delay = (send_time - now).total_seconds()

            confirmation_embed = discord.Embed(
                description=f"Wiadomość zostanie wysłana o godzinie **{send_time.strftime('%H:%M')}**",
                color=12370112
            )
            confirmation_message = await interaction.followup.send(embed=confirmation_embed)

            await asyncio.sleep(delay)
            await interaction.channel.send(embed=embed)
            await confirmation_message.delete()
        else:
            # Jeśli godzina nie została podana, wiadomość jest wysyłana od razu
            await interaction.followup.send(embed=embed)

    except ValueError:
        error_embed = discord.Embed(
            title="Błąd",
            description="Podano nieprawidłowy format godziny. Prawidłowy format to **HH:MM**",
            color=0xff1d15
        )
        await interaction.followup.send(embed=error_embed, ephemeral=True)
