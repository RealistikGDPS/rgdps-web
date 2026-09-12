# RealistikGDPS website

The public site of [RealistikGDPS](https://rgdps.ussr.pl): downloads,
leaderboards, server statistics, player profiles with rendered icons, and
account management (registration, login, password and username changes).

It is a FastAPI application rendering Jinja2 templates, built on
[poltergeist-core](https://github.com/RealistikGDPS/poltergeist-core) for
every read and write against the game's MySQL and Redis. Logging in with an
account imported from the 2.1 server re-hashes its password on the spot, so
the account then works in Geometry Dash 2.2 as well.

## Layout

```
web/api/         Routers, template rendering, cookies, dependencies
web/services/    Site-only orchestration (captcha, confirmations) over core
web/adapters/    Cloudflare Turnstile client
web/icons/       Icon rendering from the game's sprite atlases
web/templates/   Jinja2 templates
web/static/      Stylesheet, script, fonts, images
```

## Running

Requires the variables in `configuration/app.env.example`,
`configuration/mysql.env.example` and `configuration/web.env.example`, plus
`APP_STORAGE_PATH`, `MYSQL_HOST`, `MYSQL_TCP_PORT`, `REDIS_HOST`, `REDIS_PORT`
and `REDIS_DATABASE`, which the deployment's Compose stack supplies.

```bash
uv sync
make lint
make dev        # uvicorn with reload on :8000
```

### Icon assets

`WEB_ASSETS_PATH` must contain the game's `icons/` directory (the per-icon
`*-uhd.png` and `*-uhd.plist` atlases from `Resources/icons`) and, for
robots and spiders, `Robot_AnimDesc.plist` and `Spider_AnimDesc.plist` from
`Resources/`. Icons whose files are missing render as a 404; robots and
spiders fall back to the player's cube when their animation descriptions are
absent. These files are not part of this repository.

### Captcha

Registration uses Cloudflare Turnstile. With both keys empty the check is
skipped and a warning is logged at startup.

## Updating poltergeist-core

```bash
uv lock --upgrade-package poltergeist-core
```
