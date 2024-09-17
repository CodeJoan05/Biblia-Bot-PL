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

@client.tree.command(name="versions", description="Dostępne przekłady Pisma Świętego")
async def versions(interaction: discord.Interaction):
    description = [
        f'Oto dostępne przekłady Biblii: \n\n**Polskie:**\n\n`BB` - Biblia Brzeska (1563)\n`BN` - Biblia Nieświeska (1574)\n`BJW` - Biblia Jakuba Wujka (1599/1874)\n`BG` - Biblia Gdańska (1881)\n`BS` - Biblia Szwedzka (1948)\n`BP` - Biblia Poznańska (1975)\n`BW` - Biblia Warszawska (1975)\n`SZ` - Słowo Życia (1989)\n`BT` - Biblia Tysiąclecia: wydanie V (1999)\n`SNPD` - Słowo Nowego Przymierza: przekład dosłowny (2004)',
        f'Oto dostępne przekłady Biblii: \n\n`GOR` - Biblia Góralska (2005)\n`NBG` - Nowa Biblia Gdańska (2012)\n`PAU` - Biblia Paulistów (2016)\n`UBG` - Uwspółcześniona Biblia Gdańska (2017)\n`BE` - Biblia Ekumeniczna (2018)\n`SNP` - Słowo Nowego Przymierza: przekład literacki (2018)\n`TNP` - Przekład Toruński Nowego Przymierza (2020)\n`TRO` - Textus Receptus Oblubienicy (2023)\n\n**Angielskie:**\n\n`KJV` - King James Version (1611/1769)',
        f'Oto dostępne przekłady Biblii: \n\n`ASV` - American Standard Version (1901)\n`UKJV` - Updated King James Version (2000)\n\n**Niemieckie:**\n\n`LUTH` - Luther Bibel (1545)\n`SCH` - Schlachter Bibel (1951)\n\n**Łacińskie:**\n\n`VG` - Wulgata',
        f'Oto dostępne przekłady Biblii: \n\n**Greckie:**\n\n`TR` - Textus Receptus (1550/1884)\n`BYZ` - Tekst Bizantyjski (2013)\n`LXX` - Septuaginta: Morphologically Tagged Rahlfs\n\n**Hebrajskie:**\n\n`ALEP` - Aleppo Codex\n`WLC` - Westminster Leningrad Codex'
    ]
    embeds = [discord.Embed(title="Dostępne przekłady Biblii", description=desc, color=12370112) for desc in description]
    view = PaginatorView(embeds)
    await interaction.response.send_message(embed=view.initial, view=view)
