import discord
from discord.ext import commands
from typing import List
from collections import deque

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

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

@client.tree.command(name="help", description="Pomoc")
async def help(interaction: discord.Interaction):
    description = [
        f'Oto polecenia, których możesz użyć:\n\n`[księga] [rozdział]:[werset-(y)] [przekład]` - schemat komendy do uzyskania fragmentów z Biblii. Jeśli użytkownik chce uzyskać fragment z danego przekładu Pisma Świętego należy podać jego skrót. Przykład: `Jana 3:16-17 BG`. Jeśli użytkownik ustawił sobie domyślny przekład Pisma Świętego to nie trzeba podawać jego skrótu\n\n`/setversion [translation]` - ustawia domyślny przekład Pisma Świętego. Aby ustawić domyślny przekład Pisma Świętego należy podać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`\n\n`/search [text]` - służy do wyszukiwania fragmentów w danym przekładzie Biblii\n\n`/versions` - wyświetla dostępne przekłady Pisma Świętego',
        f'Oto polecenia, których możesz użyć:\n\n`/information` - wyświetla informacje o bocie\n\n`/invite` - wyświetla link z zaproszeniem\n\n`/contact` - zawiera kontakt do autora bota\n\n`/random` - wyświetla losowy werset z Biblii\n\n`/dailyverse [hour]` - wyświetla werset dnia z Biblii. Opcjonalnie można ustawić godzinę wysłania wiadomości w formacie **HH:MM**\n\n`/removeuserdata` - usuwa dane użytkownika z bazy danych\n\n`/maps [map]` - wyświetla wybraną mapę z Biblii'
    ]
    embeds = [discord.Embed(title="Pomoc", description=desc, color=12370112) for desc in description]
    view = PaginatorView(embeds)
    await interaction.response.send_message(embed=view.initial, view=view)
