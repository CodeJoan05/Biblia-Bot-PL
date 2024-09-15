import discord, sqlite3
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

# Utworzenie bazy danych SQLite

conn = sqlite3.connect('data/user_settings.db')
c = conn.cursor()

# Tworzenie tabeli przechowującej ustawienia użytkowników

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT)''')

# Komenda /removeuserdata

@client.tree.command(name="removeuserdata", description="Usuwa dane użytkownika z bazy danych")
async def removeuserdata(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_name = interaction.user.mention
    
    # Pobranie danych użytkownika przed usunięciem
    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    
    if user_data:
        # Usunięcie danych użytkownika
        c.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
        conn.commit()  # Zatwierdzenie zmian w bazie danych

        embed = discord.Embed(
            title="Usuwanie danych użytkownika",
            description=f"Usunięto dane użytkownika {user_name} z bazy danych. Aby móc w pełni korzystać z bota musisz ponownie ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`",
            color=12370112
        )
    else:
        embed = discord.Embed(
            title="Błąd",
            description="Nie znaleziono danych użytkownika w bazie danych.",
            color=0xff1d15
        )
    await interaction.response.send_message(embed=embed)