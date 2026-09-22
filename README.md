# RealistikGDPS website

The public site of [RealistikGDPS](https://rgdps.ussr.pl): downloads,
leaderboards, server statistics, player profiles with rendered icons, account
management (registration, login, password and username changes), the level
reupload tool (an official level copied under the bot account behind a
Turnstile challenge and a per-player daily allowance), the demon list (a
hand-ordered list of the hardest levels at `/demonlist`, with player-submitted
records that moderators approve and website-only list points that decay by
position) and, under `/admin`, the control room for operators.

It is a FastAPI application rendering Jinja2 templates, built on
[poltergeist-core](https://github.com/RealistikGDPS/poltergeist-core) for
every read and write against the game's MySQL and Redis. Logging in with an
account imported from the 2.1 server re-hashes its password on the spot, so
the account then works in Geometry Dash 2.2 as well.

## Layout

```
web/api/           Routers, template rendering, cookies, dependencies
web/api/admin/     One router per admin page
web/services/      Site-only orchestration (captcha, confirmations) over core
web/services/admin/  Read orchestration and bulk actions for the admin pages
web/adapters/      Cloudflare Turnstile and game server clients
web/icons/         Icon rendering from the game's sprite atlases
web/templates/     Jinja2 templates; admin/ holds the control room
web/static/        Stylesheets, scripts, fonts, images
```

## Admin area

`/admin` is visible to accounts holding the `admin.access` permission and
signs every action as the signed-in account, so the server's own permission
checks apply and each change lands in the moderation log. It covers the
dashboard, users, levels and their rating and report queues, comments,
the moderation log and bans, daily, weekly and event queues, songs, quests
and vault codes, map packs and gauntlets, the demon list (ordering needs
`demon_list.manage`, reviewing records `demon_list.review`; the seeded
`list_moderator` role holds both), roles, live server settings
(registration, level uploads, tool switches, download links, list points;
needs `admin.settings`) and a stack status page that probes MySQL, Redis, object
storage and the game server, refreshing itself every
`WEB_STATUS_POLL_SECONDS`. Rebuilding the leaderboards needs
`admin.maintenance`. The first administrator is granted by hand:

```sql
INSERT INTO user_roles (user_id, role_id) VALUES (<id>, 5);
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

## Events

Major actions (registrations, level uploads and ratings, bans, roles,
settings changes) are announced on Redis Pub/Sub channels named
`poltergeist:*`, each message carrying `"component": "rgdps-web"`. The
envelope and the event catalogue are documented in
[poltergeist-core](https://github.com/RealistikGDPS/poltergeist-core#events).

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
