# Credits / autorstwo

## Patch odbioru danych Bluetooth

Za odbiór metadanych Bluetooth z magistrali CAN odpowiada kod oparty na
projekcie:

<https://github.com/andrzejogh/convers-bt-audio>

Autor/maintainer projektu źródłowego: GitHub `andrzejogh`.

Ta część obejmuje między innymi:

- odbiór CAN ID `0x4B1`,
- składanie ramek ISO-TP,
- rozpoznawanie pól tytułu, wykonawcy i albumu,
- przekazanie danych do istniejącego magazynu mediów licznika.

Nie przypisujemy sobie autorstwa tej części. Oryginalne narzędzia są
udostępnione na licencji MIT; jej kopia znajduje się w `LICENSE_TOOLS_MIT`.

## Nasze dodatki

W tym repozytorium dodane zostały:

- renderer V5.2,
- centrowanie względem osi `X=297`,
- stałe wiersze `Y=120`, `Y=143`, `Y=166`,
- kolory wykonawcy, tytułu i albumu,
- pusta dolna linia, gdy album nie został odebrany,
- połączony pipeline VBF,
- testy, dokumentacja i zabezpieczenia kompatybilności.

## Zakres odpowiedzialności

Projekt jest nieoficjalną modyfikacją firmware Ford Convers+. Nie jest związany
z Ford Motor Company. Przed użyciem trzeba wykonać backup firmware i EEPROM
oraz posiadać realną procedurę recovery.
