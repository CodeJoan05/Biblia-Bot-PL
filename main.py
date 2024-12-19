import discord, json, re, sqlite3, os
from discord.ext import commands
from dotenv import load_dotenv

# Import komend

from commands.help import help
from commands.information import information
from commands.versions import versions
from commands.invite import invite
from commands.contact import contact
from commands.setversion import setversion
from commands.search import search
from commands.removeuserdata import removeuserdata
from commands.random import random
from commands.dailyverse import dailyverse
from commands.maps import maps

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

# Rejestracja komend

client.tree.add_command(help)
client.tree.add_command(information)
client.tree.add_command(versions)
client.tree.add_command(invite)
client.tree.add_command(contact)
client.tree.add_command(setversion)
client.tree.add_command(search)
client.tree.add_command(removeuserdata)
client.tree.add_command(random)
client.tree.add_command(dailyverse)
client.tree.add_command(maps)

# Utworzenie bazy danych SQLite

conn = sqlite3.connect('data/user_settings.db')
c = conn.cursor()

# Tworzenie tabeli przechowującej ustawienia użytkowników

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT)''')

# Akceptowane nazwy ksiąg

def Find_Bible_References(text):
    with open('resources/booknames/books.json', 'r', encoding='utf-8') as file:
        books = json.load(file)

    """ Te linijki tworzą wzorzec dla wyrażenia regularnego, który będzie używany do wyszukiwania odniesień 
    do ksiąg w tekście. Wzorzec jest tworzony na podstawie kluczy słownika books (które są nazwami ksiąg) oraz 
    skrótów tych nazw. """

    pattern = r"\b("
    pattern += "|".join(books.keys())
    pattern += r"|"
    pattern += "|".join([abbr for abbrs in books.values() for abbr in abbrs])
    pattern += r")\s+(\d+)(?::(\d+))?(?:-(\d+))?\b"

    regex = re.compile(pattern, re.IGNORECASE) # Kompiluje wzorzec do obiektu wyrażenia regularnego, który może być używany do wyszukiwania pasujących ciągów. Flaga re.IGNORECASE sprawia, że wyszukiwanie jest niewrażliwe na wielkość liter
    matches = regex.findall(text) # Używa skompilowanego wyrażenia regularnego do wyszukania wszystkich dopasowań w podanym tekście

    # Te linijki przetwarzają dopasowania, zamieniając skróty na pełne nazwy ksiąg i dodając je do listy references wraz z numerami rozdziałów i wersetów

    references = []
    for match in matches:
        full_book_name = next((book for book, abbreviations in books.items() if match[0].lower() in abbreviations), match[0])
        references.append((full_book_name, int(match[1]), int(match[2]) if match[2] else None, int(match[3]) if match[3] else None))

    return references # Zwraca listę references, która zawiera pełne nazwy ksiąg, numery rozdziałów i wersetów dla każdego dopasowania znalezionego w tekście

# Dodanie plików z Biblią; kod umożliwiający wysyłanie danej liczby wersetów

def Get_Passage(translation, book, chapter, start_verse, end_verse):

    with open('resources/booknames/english_polish.json', 'r', encoding='utf-8') as file:
        english_to_polish_books = json.load(file)

    if (start_verse == 0 or end_verse == 0) and start_verse > end_verse:
        return None

    with open(f'resources/bibles/{translation}.json', 'r') as file:
        bible = json.load(file)

    verses = list(filter(lambda x: x['book_name'] == book and x['chapter'] ==
                  chapter and x['verse'] >= start_verse and x['verse'] <= end_verse, bible))

    if len(verses) != 0:
        versesRef = str(verses[0]["verse"])
        if verses[0]["verse"] != verses[len(verses)-1]["verse"]:
            versesRef += "-"+str(verses[len(verses)-1]["verse"])
    else:
        return None

    polish_book_name = english_to_polish_books.get(book, book)

    return {"name": polish_book_name, "chapter": chapter, "verses_ref": versesRef, "verses": verses}

def Filter_Verses(verse, start_verse, end_verse):
    return verse["verse"] >= start_verse and verse["verse"] <= end_verse

# Informacje o logowaniu i aktywności na discordzie

@client.event
async def on_ready():
    print(f'Zalogowano jako {client.user}!')
    await client.change_presence(activity=discord.Activity(name='Biblię', type=discord.ActivityType.watching))
    try:
        synced = await client.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend")
    except Exception as e:
        print(e)

     # Odtworzenie ustawień użytkowników z bazy danych

    c.execute("SELECT * FROM user_settings")
    rows = c.fetchall()
    for row in rows:
        default_translations[row[0]] = row[1]

# Czcionka italic

def format_verse_text(text):
    return re.sub(r'\[([^\]]+)\]', r'*\1*', text)

# Domyślne tłumaczenie

default_translations = {}

@client.event
async def on_message(message):

    # Sprawdza, czy autor wiadomości jest tym samym użytkownikiem, który jest zalogowany jako klient (czyli bot)

    if message.author == client.user:
        return
    
    # Sprawdza, czy treść wiadomości zaczyna się od "/setversion"

    if message.content.startswith('/setversion'):
        return

    # Przypisuje identyfikator autora wiadomości do zmiennej user_id

    user_id = message.author.id 

    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()

    # Przetwarzanie wiadomości z domyślnym przekładem Biblii użytkownika
    translation = user_data[1] if user_data else None

    # Sprawdza czy wiadomość zawiera odwołanie do fragmentu Biblii
    
    BibleVerses = Find_Bible_References(message.content)
    if BibleVerses and not user_data:
        embed = discord.Embed(
            title="Ustaw domyślny przekład Pisma Świętego",
            description='Aby móc korzystać z funkcji wyszukiwania fragmentów Biblii, musisz najpierw ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`. Aby ustawić domyślny przekład Pisma Świętego należy podać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`',
            color=12370112)
        await message.channel.send(embed=embed)
    elif translation:

        # Sprawdzenie, czy wiadomość zawiera skrót przekładu na końcu

        words = message.content.split()
        last_word = words[-1]

        with open('resources/translations/bible_translations.txt', 'r') as file:
            bible_translations = [line.strip() for line in file]

        if last_word in bible_translations:
            # Jeśli podano skrót przekładu, używa tego przekładu zamiast domyślnego
            translation = last_word
            # Usuwa skrót przekładu z wiadomości
            message.content = ' '.join(words[:-1])

        await process_message_with_translation(message, translation)

async def process_message_with_translation(message, translation):
    # Przetwarzanie wiadomości z określonym przekładem Biblii
    pass

    # Wysyłanie wiadomości na podany(e) fragment(y) Biblii

    with open('resources/translations/translations.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)

    BibleJson = []
    BibleVerses = Find_Bible_References(message.content) # Wywołuje funkcję z treścią wiadomości jako argumentem

    for verse in BibleVerses:
        if verse[1] is not None and verse[2] is not None and verse[3] is not None:
            BibleJson.append(Get_Passage(
                translation, verse[0], verse[1], verse[2], verse[3]))
        elif verse[1] is not None and verse[2] is not None and verse[3] is None:
            BibleJson.append(Get_Passage(
                translation, verse[0], verse[1], verse[2], verse[2]))

    for Verses in BibleJson:

        if Verses != None and "verses" in Verses:

            header = Verses["name"]+" "+str(Verses["chapter"]) + ":" + Verses["verses_ref"]
            desc = ""

            for v in Verses["verses"]:

                desc += "**(" + str(v["verse"])+")** "+format_verse_text(v["text"]).replace("\n", " ").replace("  ", " ").strip()+" "
            desc = (desc[:4093] + '...') if len(desc) > 4093 else desc

            embed = discord.Embed(
                title=header, description=desc, color=12370112)
            embed.set_footer(text=translations[translation])
            await message.channel.send(embed=embed)
        else:
            error_embed = discord.Embed(
                title="Błąd wyszukiwania", description="Podany werset nie istnieje lub przekład Biblii nie zawiera Starego lub Nowego Testamentu", color=0xff1d15)
            await message.channel.send(embed=error_embed)

client.run(os.environ['TOKEN'])
