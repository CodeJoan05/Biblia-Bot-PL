import discord, json, re, asyncio, sqlite3, os
from discord.ext import commands
from typing import List
from collections import deque
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

# Przyciski do komend

class PaginatorView(discord.ui.View):
    def __init__(
        self, 
        embeds:List[discord.Embed]
    ) -> None:
        super().__init__(timeout=None)
        self._embeds = embeds
        self._queue = deque(embeds)
        self._initial = embeds[0]
        self._current_page = 1
        self._len = len(embeds)

        if self._len == 1:
            self.previous_page.disabled = True
            self.next_page.disabled = True

    def get_page_number(self) -> str:
        return f"Strona {self._current_page} z {self._len}"

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def previous_page(self, interaction: discord.Interaction, _):
        self._queue.rotate(1)
        embed = self._queue[0]
        if self._current_page > 1:
            self._current_page -= 1
        else:
            self._current_page = self._len
        embed.set_footer(text=self.get_page_number())
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next_page(self, interaction: discord.Interaction, _):
        self._queue.rotate(-1)
        if self._current_page < self._len:
            self._current_page += 1
        else:
            self._current_page = 1
        embed = self._queue[0]
        embed.set_footer(text=self.get_page_number())
        await interaction.response.edit_message(embed=embed)

    @property
    def initial(self) -> discord.Embed:
        embed = self._initial
        embed.set_footer(text=self.get_page_number())
        return embed

# Interaktywny przycisk do komendy /invite

class InviteView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Dodaj bota", url="twój_link_z_zaproszeniem"))

# Inicjalizacja bazy danych SQLite

conn = sqlite3.connect('user_settings.db')
c = conn.cursor()

# Tworzenie tabeli przechowującej ustawienia użytkowników

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT)''')

# Akceptowane nazwy ksiąg

def Find_Bible_References(text):
    with open('Booknames/books.json', 'r', encoding='utf-8') as file:
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

    with open('Booknames/english_polish.json', 'r', encoding='utf-8') as file:
        english_to_polish_books = json.load(file)

    if (start_verse == 0 or end_verse == 0) and start_verse > end_verse:
        return None

    with open(f'Bibles/{translation}.json', 'r') as file:
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

async def change_status():
    while True:
        await client.change_presence(activity=discord.Activity(name='Biblię', type=discord.ActivityType.watching))
        await asyncio.sleep(5)
        await client.change_presence(activity=discord.Game(name='/help'))
        await asyncio.sleep(5)

@client.event
async def on_ready():
    print(f'Zalogowano jako {client.user}!')
    client.loop.create_task(change_status())
    try:
        synced = await client.tree.sync()
        print(f"Zsynchronizowano {len(synced)}")
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

# Komenda /help

@client.tree.command(name="help", description="Pomoc")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Pomoc",
        description="Oto polecenia, których możesz użyć: \n\n`/setversion [przekład]` - ustawia domyślny przekład Pisma Świętego. Aby ustawić domyślny przekład Pisma Świętego należy podać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`\n\n`/search [słowo(a)]` - służy do wyszukiwania fragmentów w danym przekładzie Biblii zawierających określone słowo(a).\n\n`[księga] [rozdział]:[werset-(y)] [przekład]` - schemat komendy do uzyskania fragmentów z Biblii. Jeśli użytkownik chce uzyskać fragment z danego przekładu Pisma Świętego należy podać jego skrót. Przykład: `Jana 3:16-17 BG`. Jeśli użytkownik ustawił sobie domyślny przekład Pisma Świętego to nie trzeba podawać jego skrótu\n\n`/versions` - pokazuje dostępne przekłady Pisma Świętego\n\n`/information` - wyświetla informacje o bocie\n\n`/updates` - wyświetla informacje o aktualizacjach bota\n\n`/invite` - umożliwia dodanie bota na swój serwer\n\n**Jeśli nowa komenda nie jest widoczna na twoim serwerze, spróbuj ponownie dodać bota na swój serwer**",
        color=12370112)
    await interaction.response.send_message(embed=embed)

# Komenda /information 

@client.tree.command(name="information", description="Informacje o bocie")
async def information(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Informacje",
        description="**Biblia** to bot, który umożliwia czytanie Biblii w wielu językach, co pozwala na dogłębne badanie różnic między tekstami oryginalnymi a ich tłumaczeniami.\n\nBot zawiera **18** przekładów Pisma Świętego w języku polskim, **1** w języku angielskim, **1** w języku łacińskim, **2** w języku greckim oraz **1** w języku hebrajskim.\n\nAutorem bota jest: **Code Joan**\n\n**Strona internetowa:** https://biblia-bot.netlify.app/\n\nJeśli chcesz zgłosić błąd lub dać propozycję zmian w bocie skontaktuj się ze mną: **codejoan@op.pl**",
        color=12370112)
    await interaction.response.send_message(embed=embed)

# Komenda na ustawienie domyślnego przekładu Biblii - /setversion

@client.tree.command(name="setversion", description="Ustawienie domyślnego przekładu Pisma Świętego")
async def setversion(interaction: discord.Interaction, translation: str):

    with open('Translations/bible_translations.txt', 'r') as file:
        bible_translations = [line.strip() for line in file]

    if translation in bible_translations:
        default_translations[interaction.user.id] = translation

        # Zapisanie ustawień użytkownika do bazy danych
        c.execute("REPLACE INTO user_settings (user_id, default_translation) VALUES (?, ?)", (interaction.user.id, translation))
        conn.commit()
        
        with open('Translations/translations.json', 'r', encoding='utf-8') as f:
            translations = json.load(f)

        full_name = translations[translation]

        embed = discord.Embed(
            title="Ustawienie domyślnego przekładu Biblii",
            description=f'Twój domyślny przekład Biblii został ustawiony na: `{full_name}`',
            color=12370112)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="Error",
            description='Podano błędny przekład Biblii',
            color=16711680)
        await interaction.response.send_message(embed=embed)

# Komenda /versions

@client.tree.command(name="versions", description="Dostępne przekłady Pisma Świętego")
async def versions(interaction: discord.Interaction):
    description = f'**Polskie:**\n\n`BB` - Biblia Brzeska (1563)\n`BN` - Biblia Nieświeska (1574)\n`BJW` - Biblia Jakuba Wujka (1599/1874)\n`BG` - Biblia Gdańska (1881)\n`BS` - Biblia Szwedzka (1948)\n`BP` - Biblia Poznańska (1975)\n`BW` - Biblia Warszawska (1975)\n`SZ` - Słowo Życia (1989)\n`BT` - Biblia Tysiąclecia: wydanie V (1999)\n`SNPD` - Słowo Nowego Przymierza: przekład dosłowny (2004)\n`GOR` - Biblia Góralska (2005)\n`NBG` - Nowa Biblia Gdańska (2012)\n`PAU` - Biblia Paulistów (2016)\n`UBG` - Uwspółcześniona Biblia Gdańska (2017)\n`BE` - Biblia Ekumeniczna (2018)\n`SNP` - Słowo Nowego Przymierza: przekład literacki (2018)\n`TNP` - Przekład Toruński Nowego Przymierza (2020)\n`TRO` - Textus Receptus Oblubienicy (2023)\n\n**Angielskie:**\n\n`KJV` - King James Version (1611/1769)\n\n**Łacińskie:**\n\n`VG` - Wulgata\n\n**Greckie:**\n\n`TR` - Textus Receptus (1550/1884)\n`BYZ` - Tekst Bizantyjski (2013)\n\n**Hebrajskie:**\n\n`WLC` - Westminster Leningrad Codex'
    embeds = [discord.Embed(title="Dostępne przekłady Biblii", description=f'Oto dostępne przekłady Biblii: \n\n' + description[i:i+543], color=12370112) for i in range(0, len(description), 543)]
    view = PaginatorView(embeds)
    await interaction.response.send_message(embed=view.initial, view=view)

# Komenda /search

@client.tree.command(name="search", description="Wyszukiwanie fragmentów Biblii zawierających określone słowo(a)")
async def search(interaction: discord.Interaction, text: str):

    user_id = interaction.user.id
    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()

    if not user_data:
        embed = discord.Embed(
            title="Ustaw domyślny przekład Biblii",
            description='Aby korzystać z funkcji wyszukiwania fragmentów Biblii, musisz najpierw ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`. Aby ustawić domyślny przekład Pisma Świętego należy podać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`',
            color=12370112)
        await interaction.response.send_message(embed=embed)
        return

    translation = user_data[1]

    with open('Translations/translations.json', 'r', encoding='utf-8') as file:
        translations = json.load(file)

    with open('Booknames/english_polish.json', 'r', encoding='utf-8') as file:
        book_translations = json.load(file)

    embeds = []

    with open(f'Bibles/{translation}.json', 'r', encoding='utf-8') as file:
        bible = json.load(file)

    try:
        words = text.split()
        verses = []
        for verse in bible:
            if all(word in verse['text'] for word in words):
                for word in words:
                    verse['text'] = verse['text'].replace(word, f'**{word}**')
                verses.append(f"**{book_translations[verse['book_name']]} {verse['chapter']}:{verse['verse']}** \n{verse['text']} \n")
        if not verses:
            raise ValueError(f'Nie znaleziono żadnego wersetu zawierającego słowo(a) "**{text}**" w przekładzie `{translations[translation]}`')
        
    except ValueError as err:
        embed = discord.Embed(
            title="Błąd wyszukiwania",
            description=str(err),
            color=16711680)
        await interaction.response.send_message(embed=embed)
        return

    message = ''
    for verse in verses:
        if len(message) + len(verse) < 800:
            message += f"{verse}\n"
        else:
            embed = discord.Embed(
                title=f'Fragmenty z Biblii zawierające słowo(a) - *{text}*',
                description=message,
                color=12370112
            )
            embed.add_field(name="", value=f'**{translations[translation]}**')
            embeds.append(embed)
            message = f"{verse}\n"

    if message:
        embed = discord.Embed(
            title=f'Fragmenty z Biblii zawierające słowo(a) - *{text}*',
            description=message,
            color=12370112
        )
        embed.add_field(name="", value=f'**{translations[translation]}**')
        embeds.append(embed)

    view = PaginatorView(embeds)
    await interaction.response.send_message(embed=view.initial, view=view)

# Komenda /updates

@client.tree.command(name="updates", description="Aktualizacje bota")
async def updates(interaction: discord.Interaction):
    description = [
        f'**Czerwiec 2024**\n- Dodano komendę `/invite`\n- Naprawiono błąd w komendzie `/setversion`\n- Dodano komendę `/updates`\n- Dodano przyciski strzałek w wiadomości embed do komendy `/updates`\n\n**Marzec 2024**\n- Dodano przyciski strzałek w wiadomości embed do komendy `/versions`\n- Dodano przekłady Biblii: `BE`, `PAU`, `TRO`\n\n**Luty 2024**\n- Dodano komendę `/search`\n- Dodano przyciski strzałek w wiadomości embed do komendy `/search`',
        f'**Styczeń 2024**\n- Utworzono bazę danych, w której przechowuje się ustawiony przez użytkownika przekład Pisma Świętego\n\n**Grudzień 2023**\n- Dodano przekłady Biblii: `VG`, `SNP`, `SNPD`\n\n**Wrzesień 2023**\n- Dodano komendę `/setversion`\n- Dodano stopkę w wiadomości embed, która wyświetla pełną nazwę przekładu Biblii\n- Dodano czcionkę *italic*\n- Dodano przekłady Biblii: `BS`, `BT`, `GOR`',
        f'**Sierpień 2023**\n- Dodano przekłady Biblii: `TNP`, `SZ`, `BP`\n\n**Lipiec 2023**\n- Dodano przekłady Biblii: `BYZ`, `BJW`, `BN`, `BB`\n\n**Czerwiec 2023**\n- Dodano możliwość używania różnych nazw ksiąg (po polsku, angielsku i w formie skrótów)\n- Zmieniono angielskie nazwy ksiąg na polskie\n- Zmieniono typ komend na slash commands\n- Dodano przekłady Biblii: `KJV`, `BW`',
        f'**Maj 2023**\n- Dodano komendę `!versions`\n- Dodano wiadomość informującą o błędzie gdy użytkownik poda złe numery wersetów\n- Zmieniono wygląd wiadomości na embed\n- Dodano przekłady Biblii: `TR`, `WLC`\n\n**Kwiecień 2023**\n- Dodano zmieniający się status\n- Dodano wczytywanie plików z przekładami Biblii\n- Dodano komendę, w której podaje się nazwę księgi, numer rozdziału, numer(y) wersetu(ów) i skrót przekładu Biblii\n- Utworzono 2 komendy z prefiksem: `!help` i `!information`\n- Dodano przekłady Biblii: `BG`, `UBG`, `NBG`\n\n**Marzec 2023**\n- Utworzenie aplikacji bota\n- Uruchomienie aplikacji bota na Discordzie'
    ]
    embeds = [discord.Embed(title="Aktualizacje", description=desc, color=12370112) for desc in description]
    view = PaginatorView(embeds)
    await interaction.response.send_message(embed=view.initial, view=view)

# Komenda /invite

@client.tree.command(name="invite", description="Dodaj bota na swój serwer")
async def invite(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Dodaj bota na swój serwer",
        description='Aby dodać bota na swój serwer, kliknij w przycisk poniżej:',
        color=12370112)
    view = InviteView()
    await interaction.response.send_message(embed=embed, view=view)

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

    """ Pierwsza linijka wykonuje zapytanie SQL do bazy danych, szukając wszystkich ustawień dla użytkownika o 
    danym user_id. Druga linijka pobiera pierwszy rekord z wyników zapytania i przypisuje go do user_data. 
    Jeśli nie ma żadnych wyników, user_data będzie None """

    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()

    # Przetwarzanie wiadomości z domyślnym przekładem Biblii użytkownika
    translation = user_data[1] if user_data else None

    # Komenda !servers
    
    if message.content.startswith('!servers'):
        embed = discord.Embed(
            title="Liczba serwerów",
            description=f"Bot jest na **{len(client.guilds)}** serwerach",
            color=12370112)
        await message.channel.send(embed=embed)

    # Sprawdza czy wiadomość zawiera odwołanie do fragmentu Biblii
    
    BibleVerses = Find_Bible_References(message.content)
    if BibleVerses and not user_data:
        embed = discord.Embed(
            title="Ustaw domyślny przekład Biblii",
            description='Aby móc korzystać z funkcji wyszukiwania fragmentów Biblii, musisz najpierw ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`. Aby ustawić domyślny przekład Pisma Świętego należy podać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`',
            color=12370112)
        await message.channel.send(embed=embed)
    elif translation:

        # Sprawdzenie, czy wiadomość zawiera skrót przekładu na końcu

        words = message.content.split()
        last_word = words[-1]

        with open('Translations/bible_translations.txt', 'r') as file:
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

    with open('Translations/translations.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)

    BibleJson = [] # Tworzy pustą listę o nazwie BibleJson
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

            header = "**" + \
                Verses["name"]+" "+str(Verses["chapter"]) + \
                ":" + Verses["verses_ref"] + "**"
            desc = ""

            for v in Verses["verses"]:

                desc += "**(" + \
                    str(v["verse"])+")** "+format_verse_text(v["text"]).replace("\n", " ").replace("  ", " ").strip()+" "
            desc = (desc[:4093] + '...') if len(desc) > 4093 else desc

            embed = discord.Embed(
                title=header, description=desc, color=12370112)
            embed.set_footer(text=translations[translation])
            await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Błąd wyszukiwania", description="Podany(e) werset(y) nie istnieje(ą) lub przekład Biblii nie zawiera Starego lub Nowego Testamentu", color=16711680)
            await message.channel.send(embed=embed)

# Token

client.run(os.environ['TOKEN'])
