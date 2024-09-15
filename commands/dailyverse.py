import discord, datetime, asyncio, pytz, json, sqlite3
from discord.ext import commands
from discord import app_commands
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

@client.tree.command(name="dailyverse", description="Wyświetla werset(y) dnia z Biblii")
@app_commands.describe(verses="Ustaw fragment(y) z Biblii", hour="Godzina wysłania wiadomości (w formacie HH:MM)")
async def dailyverse(interaction: discord.Interaction, verses: str, hour: str = None):

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

    with open('resources/booknames/books.json', 'r', encoding='utf-8') as file:
        books_aliases = json.load(file)

    with open('resources/translations/translations.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)

    def normalize_book_name(book_name):
        book_name = book_name.strip().lower()
        
        # Sprawdza, czy nazwa księgi pasuje do pełnej lub skróconej nazwy
        for book, aliases in books_aliases.items():
            if book_name in [alias.lower() for alias in aliases]:
                return book
        return book_name

    def get_polish_book_name(english_name):
        return english_to_polish_books.get(english_name, english_name)

    def extract_book_and_remainder(text):
        text = text.strip()

        for i in range(len(text)):
            if text[i].isdigit() and (i > 0 and text[i-1] == ' '):
                # Akceptowanie nazwy księgi typu "1 Jana 1:1"
                book_name = text[:i].strip()
                remainder = text[i:].strip()
                return book_name, remainder

        if ' ' in text:
            book_name, remainder = text.split(' ', 1)
            return book_name, remainder

        return text, ""

    try:
        parsed_verses = []
        verse_title = ""

        for verse in verses.split(','):
            verse = verse.strip()

            book_name, remainder = extract_book_and_remainder(verse)
            chapter, verse_range = remainder.split(':')
            chapter = int(chapter)

            if '-' in verse_range:
                verse_start, verse_end = map(int, verse_range.split('-'))
                verse_title = f"{book_name} {chapter}:{verse_start}-{verse_end}"
            else:
                verse_start = verse_end = int(verse_range)
                verse_title = f"{book_name} {chapter}:{verse_start}"

            book_name_normalized = normalize_book_name(book_name)
            book_name_polish = get_polish_book_name(book_name_normalized)

            verse_title = f"{book_name_polish} {chapter}:{verse_start}"
            if verse_start != verse_end:
                verse_title += f"-{verse_end}"

            for entry in bible:
                if entry["book_name"] == book_name_normalized and entry["chapter"] == chapter and entry["verse"] >= verse_start and entry["verse"] <= verse_end:
                    parsed_verses.append(entry)

        if not parsed_verses:
            error_embed = discord.Embed(
                title="Błąd",
                description="Nie znaleziono podanego fragmentu",
                color=0xff1d15
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        chapter = parsed_verses[0]["chapter"]
        verses_text = " ".join([f"**({entry['verse']})** {entry['text']}" for entry in parsed_verses])
        
        embed = discord.Embed(
            title=f"{verse_title}",
            description=verses_text,
            color=12370112
        )
        embed.set_footer(text=translations[translation])

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
            confirmation_message = await interaction.followup.send(embed=confirmation_embed, ephemeral=True)

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