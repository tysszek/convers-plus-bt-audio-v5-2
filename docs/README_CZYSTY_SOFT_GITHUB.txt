DOKUMENTACJA DLA CZYSTEGO SOFTU I PUBLIKACJI NA GITHUBIE
FORD CONVERS+ 1412-FL — PATCH BT AUDIO V5.2
============================================================

Cel dokumentu
-------------

Ten plik opisuje, jak przygotować patch V5.2 mając własny, czysty plik
firmware CD oraz jak opublikować projekt w sposób możliwie bezpieczny dla
innych użytkowników.

AUTORSTWO PATCHU ODBIORU BLUETOOTH
-----------------------------------

Część odpowiedzialna za odbiór metadanych Bluetooth z CAN nie jest naszym
autorskim rozwiązaniem. Jest oparta na projekcie GitHub:

  https://github.com/andrzejogh/convers-bt-audio

Autor/maintainer projektu źródłowego: GitHub `andrzejogh`.
Oryginalne narzędzia są objęte licencją MIT. Nasze dodatki to renderer V5.2,
centrowanie, stałe wiersze, układ kolorów, opcjonalny album, pipeline VBF oraz
dokumentacja. Pełne credits powinny znajdować się w pliku CREDITS.md.

Nie jest to instrukcja dla dowolnego licznika Forda. Patch został przygotowany
dla konkretnej bazy Ford Convers+ 1412-FL i dla pliku CS7T-14C026-CD.vbf.
Inna wersja programu, inny moduł albo inny układ pamięci wymagają osobnej
analizy. Nie wolno usuwać blokad wersji z narzędzia budującego.

1. CO OZNACZA „CZYSTY SOFT”
---------------------------

Czysty soft to własny odczyt niezmodyfikowanego pliku:

  CS7T-14C026-CD.vbf

Nie należy mylić go z:
  - pełnym zrzutem pamięci procesora,
  - kopią EEPROM,
  - plikiem ED zawierającym zasoby graficzne,
  - plikiem CD z wcześniejszą modyfikacją,
  - plikiem z innego licznika lub innej wersji 1412-FL.

Przed jakąkolwiek próbą wykonaj pełny backup licznika i EEPROM. Zachowaj go
poza katalogiem projektu. Nie publikuj w internecie EEPROM-u, numeru VIN,
pełnych zrzutów pamięci ani plików zawierających dane konkretnego samochodu.

2. WYMAGANA ZGODNOŚĆ BAZY
--------------------------

Obecny builder jest celowo zablokowany sumą SHA-256. Akceptuje wyłącznie
rozpoznaną bazę:

  CS7T-14C026-CD.vbf
  SHA-256: 668e7c09c3c09cbd2c769d17acc5870ff28cb39a2cf04143e6f8b34c8cbf1dda

Jeżeli suma jest inna, builder ma się zatrzymać. Nie wolno wtedy „na siłę”
zmieniać wartości SOURCE_SHA ani omijać sprawdzeń. Inny plik może mieć inne
adresy funkcji, inne bufory lub inną długość i patch może uszkodzić licznik.

Sprawdzenie w Linux/macOS/WSL:

  sha256sum CS7T-14C026-CD.vbf

Sprawdzenie w PowerShell:

  Get-FileHash .\CS7T-14C026-CD.vbf -Algorithm SHA256

Dodatkowo plik powinien być prawidłowym VBF. W projekcie kontrolowane są:
  - adres bazowy payloadu 0x5000,
  - długość payloadu 0xfb000,
  - poprawność kontroli VBF.

3. WYMAGANE PLIKI DO ODTWORZENIA BUILD
---------------------------------------

Przykładowy układ katalogów projektu:

  projekt/
    build_bt_center_test.py
    CONVERS_1412_BT_SWEEP_MENU_PL/
      01_DO_WGRANIA/
        CS7T-14C026-CD.vbf
        7M2T-14C025-AA.vbf
    vendor_convers_bt/
      tools/
        vbf_tool.py
        emulate.py
        pozostałe pliki narzędzi analitycznych

Plik CD musi być własną, czystą kopią zgodną z SHA-256 powyżej. Bootloader AA
używany przy budowaniu i programowaniu musi być zgodny z dotychczasową
procedurą dla tego licznika:

  7M2T-14C025-AA.vbf
  SHA-256: 61d445cbee401500a132b1ea904a398563c6a0a385142158ca646c00e1cbc2ab

Nie należy pobierać przypadkowego AA z innego pakietu.

4. ŚRODOWISKO DO BUDOWANIA
---------------------------

Potrzebne są:
  - Python 3,
  - moduł Unicorn używany przez test ARM,
  - pliki narzędzi z katalogu vendor_convers_bt/tools,
  - skrypt build_bt_center_test.py.

Przykładowa instalacja modułu w osobnym środowisku:

  python3 -m venv .venv
  . .venv/bin/activate
  python3 -m pip install --upgrade pip
  python3 -m pip install unicorn

W Windows można użyć odpowiednika:

  py -m venv .venv
  .venv\Scripts\activate
  py -m pip install unicorn

Dokładna wersja Pythona i modułu powinna być zapisana w README projektu,
jeżeli patch będzie rozwijany publicznie. Sam builder nie programuje licznika.
Tworzy pliki wynikowe i wykonuje testy kontrolne.

5. URUCHOMIENIE BUILDERA
------------------------

Po przygotowaniu katalogów uruchom z katalogu projektu:

  python3 build_bt_center_test.py

Builder powinien:
  1. sprawdzić SHA-256 źródłowego CD i bootloadera AA;
  2. sprawdzić strukturę oraz kontrolę VBF;
  3. wstawić patch renderera BT Audio w dozwolonym obszarze;
  4. uruchomić test ARM dla dwóch trybów ekranu;
  5. sprawdzić dwa i trzy wiersze, album obecny/nieobecny oraz puste pola;
  6. wykonać regresję łańcucha metadanych CAN -> magazyn -> renderer;
  7. sprawdzić stos, rejestry i zakres zmienionych bajtów;
  8. zbudować poprawny plik CD z nowymi sumami VBF;
  9. skopiować niezmieniony AA oraz bazę powrotu;
 10. wygenerować AUDYT.json i SHA256SUMS.txt.

Jeżeli pojawi się błąd „Wrong input version: abort”, należy przerwać pracę.
Nie wolno usuwać tego zabezpieczenia.

6. CO DOKŁADNIE ZMIENIA PATCH
-----------------------------

Patch dotyczy wyłącznie kodu CD. Nie zmienia odbioru danych Bluetooth/CAN ani
plików ED z grafikami.

Renderer V5.2 ustawia:
  - wykonawca: biały, Y=120;
  - tytuł: szary, Y=143;
  - album: szary, Y=166, wyłącznie gdy istnieje.

Wszystkie linie w obserwowanym układzie korzystają z osi centrowania X=297.
Jeżeli albumu nie ma, dolna linia jest pusta, a wykonawca i tytuł nie zmieniają
położenia. Lokalny napis „Tytuł” i numer utworu nie są rysowane.

Ważne: czerwone logo i grafika tła nie są przez ten patch przesuwane ani
ponownie budowane. Są zasobami ED, które pozostają w liczniku.

7. WERYFIKACJA WYNIKU BUILD
----------------------------

Po zakończeniu sprawdź:

  cd BT_AUDIO_UKLAD_V5_2_STALE_POZYCJE_Z_BOOTLOADEREM
  sha256sum -c SHA256SUMS.txt

Sprawdź również archiwum:

  unzip -t BT_AUDIO_UKLAD_V5_2_STALE_POZYCJE_Z_BOOTLOADEREM.zip

Wynikowy CD powinien mieć sumę:

  4553f72f4a2527b890b92c08be5ab3d4c1f69c2c2926bdce6179acab143af9c7

Jeżeli wynik ma inną sumę, nie zakładaj automatycznie, że jest poprawny.
Najpierw sprawdź wersję źródła, narzędzia i wszystkie pliki wejściowe.

8. PROGRAMOWANIE NA LICZNIKU
----------------------------

Builder nie zastępuje instrukcji programatora. Wgrywanie należy wykonać
wyłącznie sprawdzoną procedurą dla konkretnego interfejsu:

  1. stabilne zasilanie i pełny backup;
  2. załadowanie AA/SBL, jeżeli wymaga tego procedura;
  3. zapis właściwego CS7T-14C026-CD.vbf;
  4. pełna weryfikacja i kontrolowany restart;
  5. test BT Audio, radia, USB, lewej części ekranu i testu wskazówek.

Nie należy wgrywać ED tylko dlatego, że znajduje się w innej paczce. V5.2
zmienia CD. AA może być wymagany przy każdym programowaniu, ale należy go
ładować dokładnie w taki sposób, jaki działał wcześniej z danym narzędziem.

9. TEST AKCEPTACYJNY DLA NOWEGO UŻYTKOWNIKA
--------------------------------------------

Po uruchomieniu licznika sprawdź kolejno:
  - utwór z wykonawcą, tytułem i albumem;
  - utwór bez albumu;
  - zmianę utworu i odświeżenie metadanych;
  - długi tytuł — V5.2 nie dodaje przewijania;
  - radio -> BT -> USB/CD;
  - menu polskie i test wskazówek;
  - lewą część ekranu oraz Lane Assist;
  - brak napisów „Tytuł” i numeru.

Wynik należy udokumentować zdjęciem oraz podać SHA-256 wgranych plików.
Jeżeli kolejność, pozycja lub działanie jest inne, nie należy publikować
wyniku jako potwierdzonego.

10. ZASADY PUBLIKACJI NA GITHUBIE
----------------------------------

Zalecana zawartość publicznego repozytorium:
  - README.md z zakresem kompatybilności;
  - skrypt budujący i testy;
  - dokumentacja niniejszego patcha;
  - AUDYT.json i oczekiwane sumy;
  - przykładowy raport z testów;
  - instrukcja recovery i wyraźne ostrzeżenia.

Nie publikuj:
  - VIN-u ani EEPROM-u;
  - pełnego zrzutu pamięci licznika;
  - pliku z danymi konkretnego auta;
  - cudzych kopii firmware bez sprawdzenia praw do ich udostępniania.

Firmware Forda może podlegać ograniczeniom właściciela praw. Najbezpieczniej
publikować własne skrypty, dokumentację, sumy, opis zmian i testy, a użytkownik
niech dostarczy własny plik bazowy. Jeżeli udostępniasz binaria, sprawdź przed
publikacją, czy masz do tego prawo.

README na GitHubie powinno jasno informować:
  - dla jakiego modelu i wersji jest patch;
  - jaka jest wymagana suma źródła;
  - że inna suma oznacza STOP;
  - że patch nie jest oficjalnym oprogramowaniem Forda;
  - że autor nie gwarantuje bezawaryjnego programowania;
  - że użytkownik odpowiada za backup, zasilanie i recovery;
  - że V5.2 wymaga potwierdzenia na konkretnym liczniku.

Do zgłoszenia problemu warto wymagać:
  - numeru wersji licznika;
  - SHA-256 pliku wejściowego i wynikowego;
  - użytego interfejsu/programatora;
  - informacji, czy AA był ładowany;
  - zdjęcia ekranu;
  - informacji, czy licznik nadal komunikuje się po CAN.

11. LICENCJA I ODPOWIEDZIALNOŚĆ
--------------------------------

Licencję można nadać skryptom i dokumentacji, ale nie należy automatycznie
nadawać jej firmware producenta. W repozytorium trzeba rozdzielić własny kod
i opis od plików dostarczonych przez użytkownika.

Patch jest eksperymentalną modyfikacją firmware samochodowego. Nawet poprawny
test programowy i poprawne CRC nie gwarantują bezpiecznego flashowania. Przed
publikacją należy pozostawić ostrzeżenie o możliwości utraty komunikacji i
konieczności posiadania realnej procedury recovery.

KONIEC
============================================================
