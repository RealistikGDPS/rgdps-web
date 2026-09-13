import os

APP_COMPONENT = os.environ["APP_COMPONENT"]

# Behind a reverse proxy the socket peer is the proxy; the real client address
# then arrives in the forwarded headers, which are only believed when this is on.
APP_TRUST_PROXY_HEADERS = os.environ["APP_TRUST_PROXY_HEADERS"] == "true"

WEB_SITE_NAME = os.environ["WEB_SITE_NAME"]
WEB_COOKIE_SECURE = os.environ["WEB_COOKIE_SECURE"] == "true"

# Empty keys switch the captcha off. That is a product decision for local
# development only; production sets both.
TURNSTILE_SITE_KEY = os.environ["TURNSTILE_SITE_KEY"]
TURNSTILE_SECRET_KEY = os.environ["TURNSTILE_SECRET_KEY"]
TURNSTILE_TIMEOUT_SECONDS = float(os.environ["TURNSTILE_TIMEOUT_SECONDS"])

# The game server as reached on the internal network, for the status page.
WEB_GAME_SERVER_URL = os.environ["WEB_GAME_SERVER_URL"].rstrip("/")
WEB_GAME_SERVER_TIMEOUT_SECONDS = float(os.environ["WEB_GAME_SERVER_TIMEOUT_SECONDS"])
WEB_STATUS_POLL_SECONDS = int(os.environ["WEB_STATUS_POLL_SECONDS"])

# The game's Resources/icons directory plus the robot and spider animation
# descriptions, and which texture quality of them to read.
WEB_ASSETS_PATH = os.environ["WEB_ASSETS_PATH"]
WEB_ICON_QUALITY = os.environ["WEB_ICON_QUALITY"]
WEB_ICON_CACHE_SIZE = int(os.environ["WEB_ICON_CACHE_SIZE"])
