# Biblijny bot na Discorda - PL

## Instalacja pakietów:

* Wpisz w terminalu następujące komendy:

``` python
pip install discord.py
```

``` python
pip install asyncio
```

``` python
pip install pysqlite3
```

``` python
pip install python-dotenv
```

## Utwórz plik .env z taką strukturą:

``` python
TOKEN='tu wklej token bota'
```
## Wklej swój link z zaproszeniem:

Linka z zaproszeniem należy utworzyć w **Discord Developer Portal**
1. Wejdź w aplikację bota
2. Kliknij w zakładkę **OAuth2**
3. W **SCOPES** zaznacz `bot` i `applications.commands`
4. W **BOT PERMISSIONS** zaznacz następujące uprawnienia:
* Read Messages/View Channels
* Send Messages
* Send Messages in Threads
* Use Slash Commands
* Manage Messages

``` python
self.add_item(discord.ui.Button(label="Dodaj bota", url="twój_link_z_zaproszeniem"))
```

## Baza danych

W folderze `data` zostanie utworzona baza danych w pliku `user_settings.db` gdy pierwszy użytkownik ustawi domyślny przekład Pisma Świętego

## Uruchomienie bota:

* Wpisz w terminalu następującą komendę:

``` python
python main.py
```

## O bocie: 

Bot zawiera przekłady Pisma Świętego w **języku polskim, angielskim, niemieckim, łacińskim, greckim i hebrajskim**

## **Lista komend:**

`/help` - instrukcja obsługi bota

`[księga] [rozdział]:[werset-(y)] [przekład]` - schemat komendy do uzyskania fragmentów z Biblii. Jeśli użytkownik chce uzyskać fragment z danego przekładu Pisma Świętego należy podać jego skrót. Przykład: `Jana 3:16-17 BG`. Jeśli użytkownik ustawił sobie domyślny przekład Pisma Świętego to nie trzeba podawać jego skrótu

`/setversion [translation]` - ustawia domyślny przekład Pisma Świętego. Aby ustawić domyślny przekład Pisma Świętego należy wpisać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`

`/search [text]` - służy do wyszukiwania fragmentów w danym przekładzie Biblii

`/versions` - wyświetla dostępne przekłady Pisma Świętego

`/information` - wyświetla informacje o bocie

`/invite` - wyświetla link z zaproszeniem

`/contact` - zawiera kontakt do autora bota

`/random` - wyświetla losowy werset z Biblii

`/dailyverse [hour]` - wyświetla werset dnia z Biblii. Opcjonalnie można ustawić godzinę wysłania wiadomości w formacie **HH:MM**

`/removeuserdata` - usuwa dane użytkownika z bazy danych

`/maps [map]` - wyświetla wybraną mapę z Biblii

**Aby móc korzystać z funkcji wyszukiwania fragmentów Biblii, musisz najpierw ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`**

## Informacje

<p>Pliki z przekładami Biblii pochodzą z:</p>

* https://www.biblesupersearch.com/bible-downloads/
* https://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles

<p>Część polskich przekładów Biblii zawiera zawartość ze strony:</p>

* https://web.rbiblia.toborek.info/

## **Strona internetowa:** 

* https://biblia-bot.netlify.app/
