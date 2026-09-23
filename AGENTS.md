# Shipwright web fork

A fork of [HarbourMasters/Shipwright](https://github.com/HarbourMasters/Shipwright) (Ship of Harkinian) that adds a WebAssembly build, so the game runs in a browser tab from a static host like GitHub Pages. The web port follows [Ghostship](https://github.com/HarbourMasters/Ghostship)'s approach.

## Direction

- Stability over new features: `master` tracks the latest upstream release tag, never upstream `develop`. Moving to a new release is a rebase of our commits onto the new tag.
- Keep the diff against upstream small and behind `EMSCRIPTEN` / `__EMSCRIPTEN__`, so desktop builds are unchanged and rebases stay cheap.
- The browser build must run on low-end devices and Safari: prefer less memory and fewer threads over features.
- Never commit or upload a ROM, or any `oot.o2r` / `oot-mq.o2r` made from one. Players supply their own ROM in the page. `soh.o2r` holds no ROM data and is fine to ship.

## Workflow

- `master` is the default branch. Every change lands through a PR into `master`; nothing is sent upstream.
- `project516-review-bot` reviews PRs. `generate-builds` CI must be green, including `build-web`.
- `libultraship` points at `Project516/libultraship`, branch `soh-<version>-web`: upstream's pinned commit plus the Ghostship web commits.
- On a Raspberry Pi, build with a low `-j` under a memory guard; a full parallel emscripten build can lock the machine up.

## Glossary

- **soh.o2r**: SoH's own assets (fonts, shaders, custom textures). Built natively by the `GenerateSohOtr` target and preloaded into the web build.
- **oot.o2r / oot-mq.o2r**: game assets extracted from the player's ROM. In the browser they are made in the page by ZAPD and stored in IndexedDB.
- **ZAPD**: the asset extractor, linked into the game as `ZAPDLib`.
- **Asyncify**: the Emscripten transform that lets the blocking game loop yield to the browser each frame. `soh/soh/web/asyncify-remove.txt` lists code that never yields.
- **IDBFS**: Emscripten's IndexedDB-backed filesystem, mounted at `/storage` for saves, config and extracted archives.
