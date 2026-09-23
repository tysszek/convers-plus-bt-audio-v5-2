# Notice and attribution

The Bluetooth CAN receive patch and the VBF helper tools are derived from
`andrzejogh/convers-bt-audio`:

<https://github.com/andrzejogh/convers-bt-audio>

Their original MIT license is included as `LICENSE_TOOLS_MIT`.

## Who made which part

The Bluetooth metadata receive path — including the CAN `0x4B1` reception,
ISO-TP reassembly and dispatch into the existing media store — comes from the
upstream project and is not claimed as our original work:

<https://github.com/andrzejogh/convers-bt-audio>

Upstream author/maintainer: GitHub user `andrzejogh`.

Our additions are the V5.2 renderer layout, fixed centering, artist/title/
optional-album rows, the combined VBF pipeline and the accompanying Polish
documentation.

The V5.2 fixed-layout renderer and the additional documentation in this
patch-kit are experimental work for the Ford Convers+ 1412-FL target. They do
not include Ford firmware, VIN data, EEPROM dumps, or a flashing utility.
