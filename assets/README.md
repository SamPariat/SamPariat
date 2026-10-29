# Profile assets

| File | What it is |
| --- | --- |
| `banner-dark.svg` / `banner-light.svg` | The README header: a terminal window with an oh-my-zsh agnoster prompt on a 1280×360 panel (`<picture>` picks one by theme) |
| `roundup-card-dark.svg` / `roundup-card-light.svg` | The featured-project card for [roundup](https://github.com/SamPariat/roundup) |
| `cinesuggest-card-dark.svg` / `cinesuggest-card-light.svg` | The featured-project card for [CineSuggest](https://github.com/SamPariat/movie-recommendation-sm) |
| `experience-dark.svg` / `experience-light.svg` | The experience timeline; the current job's dot pulses |
| `stack-dark.svg` / `stack-light.svg` | The stack, grouped into client, backend and infra |
| `linkedin-dark.svg` / `linkedin-light.svg` | The LinkedIn link under the banner |
| `summary-dark.svg` / `summary-light.svg` | The one-line summary under the LinkedIn link |
| `nav-<section>-dark.svg` / `-light.svg` | One pill per section link (experience, stack, featured); separate files so each can be its own link |
| `divider.svg` | A blue → mauve → sky rule for section breaks |

## Colours

[Catppuccin](https://catppuccin.com/palette) Macchiato for dark and Latte for light.

| Token | Dark (Macchiato) | Light (Latte) |
| --- | --- | --- |
| bg | `#24273a` base | `#dce0e8` crust |
| panel | `#1e2030` mantle | `#eff1f5` base |
| fg | `#cad3f5` text | `#4c4f69` text |
| comment | `#6e738d` overlay0 | `#9ca0b0` overlay0 |
| blue | `#8aadf4` | `#1e66f5` |
| mauve | `#c6a0f6` | `#8839ef` |
| sky | `#91d7e3` | `#04a5e5` |
| green | `#a6da95` | `#40a02b` |

## How these were made

The text is [Iosevka](https://github.com/be5invis/Iosevka) (SIL Open Font License, see `OFL-Iosevka.txt`). It's outlined to SVG paths so it looks the same everywhere without loading a font. HarfBuzz shaped the text and fontTools outlined it, at weights Regular and Bold. The cursor in the banner blinks with an SVG `<animate>`.

The stack card and the LinkedIn link use icons from [Catppuccin for VSCode Icons](https://github.com/catppuccin/vscode-icons) (MIT): Macchiato icons in the dark card, Latte in the light one, inlined into the SVG. The set has no icons for Expo or LinkedIn, so those two are drawn in the same style: 16 px, 1 px rounded strokes. PostgreSQL and Redis share the generic database icon, Node.js uses the npm icon and AWS the AWS folder icon.

## Rebuilding

Every SVG here comes from `scripts/build.py`. Edit the data at the top of it (`THEMES`, `PROJECTS`, `STACK`, `EXPERIENCE`, `NAV`) and run:

```sh
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/build.py assets
```

It needs Iosevka Nerd Font installed in `~/Library/Fonts`. The Catppuccin icons are vendored in `scripts/icons/` with their MIT licence.
