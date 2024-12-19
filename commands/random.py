import discord, sqlite3, json, re
from discord.ext import commands
from random import choice, randint

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

# Utworzenie bazy danych SQLite

conn = sqlite3.connect('data/user_settings.db')
c = conn.cursor()

# Tworzenie tabeli przechowującej ustawienia użytkowników

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT)''')

# Czcionka italic

def format_verse_text(text):
    return re.sub(r'\[([^\]]+)\]', r'*\1*', text)

@client.tree.command(name="random", description="Wyświetla losowy werset z Biblii")
async def random(interaction: discord.Interaction):

    await interaction.response.defer()

    user_id = interaction.user.id
    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()

    if not user_data:
        embed = discord.Embed(
            title="Ustaw domyślny przekład Pisma Świętego",
            description='Aby korzystać z funkcji wyszukiwania fragmentów Biblii, musisz najpierw ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`. Aby ustawić domyślny przekład Pisma Świętego należy podać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`',
            color=12370112)
        await interaction.followup.send(embed=embed)
        return

    translation = user_data[1]
    
    with open(f'resources/bibles/{translation}.json', 'r') as file:
        bible = json.load(file)

    with open('resources/booknames/english_polish.json', 'r', encoding='utf-8') as file:
        english_to_polish_books = json.load(file)

    with open('resources/translations/translations.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    count = randint(1, 10)
    
    # Losowy werset jako punkt początkowy
    random_start = choice(bible)

    # Nazwa księgi i numer rozdziału
    book_name = random_start["book_name"]
    chapter_number = random_start["chapter"]

    # Filtruje wersety do tej samej księgi i rozdziału
    same_chapter_verses = [
        verse for verse in bible if verse["book_name"] == book_name and verse["chapter"] == chapter_number
    ]

    # Sortuje wersety według numeru wersetu
    same_chapter_verses.sort(key=lambda x: x["verse"])

    # Znajduje pozycję startową
    start_index = same_chapter_verses.index(random_start)
    
    # Wybiera kolejne wersety od punktu startowego
    selected_verses = same_chapter_verses[start_index:start_index + count]

    verses_text = ""

    polish_book_name = english_to_polish_books.get(book_name, book_name)
    
    first_verse_number = selected_verses[0]["verse"]
    last_verse_number = selected_verses[-1]["verse"]

    for selected_verse in selected_verses:
        verse_number = selected_verse["verse"]
        text = selected_verse["text"]

        verses_text += f"**({verse_number})** {format_verse_text(text)} "

    if first_verse_number == last_verse_number:
        title = f"{polish_book_name} {chapter_number}:{first_verse_number}"
    else:
        title = f"{polish_book_name} {chapter_number}:{first_verse_number}-{last_verse_number}"

    embed = discord.Embed(
        title=title,
        description=verses_text,
        color=12370112
    )
    embed.set_footer(text=translations[translation])

    await interaction.followup.send(embed=embed)
