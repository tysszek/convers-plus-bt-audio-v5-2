# Ford Convers+ BT Audio — patch-kit V5.2

Patch dla własnego pliku firmware Ford Convers+ 1412-FL. Łączy dwa etapy:

1. odbiera metadane Bluetooth z CAN i przekazuje je do magazynu mediów,
2. wyświetla wykonawcę, tytuł i opcjonalny album w stałych, wyśrodkowanych wierszach.

## Autorstwo

To jest projekt pochodny. Część odpowiedzialna za odbiór metadanych Bluetooth
z CAN nie jest naszym autorskim rozwiązaniem. Jest oparta na projekcie
[`andrzejogh/convers-bt-audio`](https://github.com/andrzejogh/convers-bt-audio),
którego autorem/maintainerem jest użytkownik GitHub `andrzejogh`.

Oryginalny kod i narzędzia są objęte licencją MIT — szczegóły znajdują się w
`LICENSE_TOOLS_MIT`. Naszym dodatkiem jest renderer V5.2, stałe pozycje,
centrowanie, układ kolorów, opcjonalny album, pipeline VBF i dokumentacja.
Pełne rozdzielenie autorstwa znajduje się w `CREDITS.md`.

## Efekt na ekranie

```text
Wykonawca — biały — górna linia
Tytuł     — szary — środkowa linia
Album     — szary — dolna linia, jeżeli został odebrany
```

Wersja V5.2 używa osi optycznej `X=297`. Gdy albumu nie ma, dolny wiersz
pozostaje pusty, a tytuł nie zmienia pozycji. Lokalny napis `Tytuł` i numer
utworu nie są rysowane.

## Kompatybilność

To repozytorium nie jest uniwersalnym patchem do każdego Convers+. Celuje w:

- Ford Convers+ IPC,
- programową partycję `CS7T-14C026-CD`,
- bazę 1412-FL z układem adresów opisanym w skryptach,
- Bluetooth metadata CAN ID `0x4B1`, źródło `0x12`.

Skrypty sprawdzają oczekiwane bajty hooków i przerywają przy niezgodności.
Nie usuwaj tych zabezpieczeń. Inna wersja firmware wymaga osobnego portu i
osobnego testu na fizycznym liczniku.

Jednokomendowy patcher dodatkowo wymaga dokładnej sumy SHA-256 payloadu
`0x5000`:

```text
9c4b3b051a9dd1705d2acd27658d25fb71a52f5c2a20f5595f4885016a3661a1
```

To jest blokada kompatybilności dla znanej czystej bazy 1412-FL. Różny hash
oznacza STOP, nawet jeżeli nazwa pliku i numer partycji wyglądają poprawnie.

## Bezpieczeństwo

To modyfikuje firmware licznika. Zawsze przed pracą:

- wykonaj i sprawdź pełny backup firmware oraz EEPROM;
- zachowaj własny oryginalny VBF poza repozytorium;
- nie publikuj VIN-u, EEPROM-u ani pełnego zrzutu pamięci;
- zapewnij stabilne zasilanie programujące;
- przygotuj sprawdzoną procedurę recovery/JTAG/BDM;
- testuj na postoju.

Patch-kit nie programuje licznika. Tworzy nowy VBF. Bootloader AA nie jest tu
dołączony — użyj własnego, zgodnego z licznikiem i z dotychczasową procedurą.

## Użycie — jedna komenda

Nie umieszczaj własnego firmware w repozytorium. Na komputerze trzymaj go w
osobnym katalogu i uruchom:

```bash
python3 tools/patch_vbf_bt_audio_v5_2.py \
  /sciezka/do/CS7T-14C026-CD.vbf \
  /sciezka/do/CS7T-14C026-CD_BT_AUDIO_V5_2.vbf
```

W Windows:

```powershell
py tools\patch_vbf_bt_audio_v5_2.py `
  C:\sciezka\CS7T-14C026-CD.vbf `
  C:\sciezka\CS7T-14C026-CD_BT_AUDIO_V5_2.vbf
```

Program:

1. sprawdzi strukturę i CRC wejściowego VBF;
2. rozpakowuje tylko payload programu `0x5000`;
3. nakłada patch odbioru Bluetooth z `apply_patch_v3.py`;
4. nakłada bezpieczne przesunięcie bufora tytułu z `apply_render.py`;
5. nakłada renderer V5.2;
6. pakuje wynik z nowym CRC16 i CRC32;
7. nie nadpisuje pliku źródłowego i nie wykonuje flashowania.

Domyślny CAN ID to `0x4B1`. Eksperymentalne przekierowanie można wskazać
parametrem, ale tylko gdy przechwycenie magistrali potwierdzi inny ID:

```bash
python3 tools/patch_vbf_bt_audio_v5_2.py input.vbf output.vbf --canid 0x4C6
```

Inny CAN ID musi być już akceptowany przez sprzętową tablicę odbioru. Sam
parametr nie rekonfiguruje kontrolera CAN.

## Użycie etapami

Jeżeli chcesz zobaczyć każdy etap osobno:

```bash
python3 tools/vbf_tool.py verify input.vbf
python3 tools/vbf_tool.py unpack input.vbf main.bin
python3 tools/apply_patch_v3.py main.bin main_bt.bin
python3 tools/apply_render.py main_bt.bin main_bt_render.bin
python3 tools/apply_layout_v5_2.py main_bt_render.bin main_patched.bin
python3 tools/vbf_tool.py pack input.vbf main_patched.bin output.vbf
python3 tools/vbf_tool.py verify output.vbf
```

Każdy skrypt sprawdza swoje punkty kontrolne. Błąd `mismatch`, `unsupported`
albo `Wrong input version` oznacza STOP — nie omijaj zabezpieczenia.

## Test lokalny bez firmware i bez samochodu

Sam renderer można sprawdzić bez żadnego pliku Forda:

```bash
python3 tools/apply_layout_v5_2.py --self-test
```

Opcjonalne testy emulatora z upstreamowego projektu wymagają:

```bash
python3 -m pip install -r requirements-optional.txt
```

Nie zastępują one testu na fizycznym liczniku.

## Ograniczenia

- Maksymalna długość metadanych zależy od modułu Bluetooth i architektury
  licznika; praktycznie jest to 19 znaków pola.
- V5.2 nie dodaje przewijania długich tytułów.
- Album jest opcjonalny i zależy od tego, czy telefon/moduł go wysyła.
- Patch nie zmienia grafiki ED, lewej części ekranu, Lane Assist, radia,
  USB ani testu wskazówek.
- V5.2 ma testy programowe i bazuje na działającym łańcuchu Bluetooth, ale
  wariant zbudowany z czystego VBF wymaga potwierdzenia na konkretnym aucie.

## Dlaczego tytuł może nadal nie przyjść

Patch oczekuje metadanych na `0x4B1`. Jeśli telefon, moduł Bluetooth albo
radio nie wysyła tekstu na ten CAN ID, renderer nie ma czego wyświetlić.
Najpierw sprawdź magistralę i użyj testu z dokumentacji upstreamowej.
Test ścieżki USB może potwierdzić, że sam ekran i magazyn mediów działają.

## Zawartość

```text
tools/
  patch_vbf_bt_audio_v5_2.py  — pełny pipeline VBF -> V5.2 VBF
  apply_patch_v3.py           — odbiór 0x4B1 i zapis metadanych
  apply_render.py             — bezpieczny bufor tytułu
  apply_layout_v5_2.py        — wykonawca/tytuł/album, stałe Y i X
  vbf_tool.py                 — unpack/pack/CRC VBF
  make_test_frames.py         — pomoc do testów CAN
docs/
  HOW_IT_WORKS_UPSTREAM.md
  FLASHING_UPSTREAM.md
  TESTING_UPSTREAM.md
tests/
  test_layout_v5_2.py
```

## Publikowanie

Repozytorium powinno zawierać skrypty i dokumentację, ale nie prywatne dumpy.
Firmware producenta udostępniaj wyłącznie wtedy, gdy masz do tego prawa.
W zgłoszeniu problemu podawaj wersję, SHA-256 pliku, użyty programator oraz
zdjęcie wyniku — nigdy VIN-u ani EEPROM-u.

## Pochodzenie narzędzi i autorstwo

Etap odbioru Bluetooth i narzędzia VBF są oparte na projekcie:

<https://github.com/andrzejogh/convers-bt-audio>

Oryginalna licencja MIT i informacja o autorstwie znajduje się w
`LICENSE_TOOLS_MIT`. Renderer V5.2 oraz dokumentacja układu są dodatkiem do
tego patch-kitu. Projekt nie jest związany z Ford Motor Company.
