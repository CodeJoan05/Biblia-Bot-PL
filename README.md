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

## Uruchomienie bota:

* Wpisz w terminalu następującą komendę:

``` python
python main.py
```

## O bocie: 

Bot zawiera przekłady Pisma Świętego w **języku polskim, angielskim, łacińskim, greckim i hebrajskim**

## **Lista komend:**

`/help` - instrukcja obsługi bota

`/setversion [przekład]` - ustawia domyślny przekład Pisma Świętego. Aby ustawić domyślny przekład Pisma Świętego należy wpisać jego skrót. Wszystkie skróty przekładów są dostępne w `/versions`

`/search [słowo(a)]` - służy do wyszukiwania fragmentów Biblii zawierających określone słowo(a)

`[księga] [rozdział]:[werset-(y)] [przekład]` - schemat komendy do uzyskania fragmentów z Biblii. Jeśli użytkownik chce uzyskać fragment z danego przekładu Pisma Świętego należy podać jego skrót. Przykład: `Jana 3:16-17 BG`. Jeśli użytkownik ustawił sobie domyślny przekład Pisma Świętego to nie trzeba podawać jego skrótu.

`/versions` - pokazuje dostępne przekłady Pisma Świętego

`/information` - wyświetla informacje na temat bota

`/updates` - wyświetla informacje o aktualizacjach bota

**Aby móc korzystać z funkcji wyszukiwania fragmentów Biblii, musisz najpierw ustawić domyślny przekład Pisma Świętego za pomocą komendy `/setversion`**

## Informacje

<p>Pliki z przekładami Biblii pochodzą z:</p>

* https://www.biblesupersearch.com/bible-downloads/
* https://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles

<p>Część polskich przekładów Biblii zawiera zawartość ze strony:</p>

* https://web.rbiblia.toborek.info/

## **Strona internetowa:** 

* https://biblia-bot.netlify.app/
