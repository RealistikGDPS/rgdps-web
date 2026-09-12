from gdformat.enums import Difficulty
from gdformat.enums import Length
from gdformat.enums import ModLevel
from gdformat.enums import Rating
from poltergeist_core.resources import LeaderboardKind

from web.icons import IconKind

_DIFFICULTY = {
    Difficulty.NA: "Unrated",
    Difficulty.AUTO: "Auto",
    Difficulty.EASY: "Easy",
    Difficulty.NORMAL: "Normal",
    Difficulty.HARD: "Hard",
    Difficulty.HARDER: "Harder",
    Difficulty.INSANE: "Insane",
    Difficulty.EASY_DEMON: "Easy Demon",
    Difficulty.MEDIUM_DEMON: "Medium Demon",
    Difficulty.HARD_DEMON: "Hard Demon",
    Difficulty.INSANE_DEMON: "Insane Demon",
    Difficulty.EXTREME_DEMON: "Extreme Demon",
}
_RATING = {
    Rating.NONE: "",
    Rating.EPIC: "Epic",
    Rating.LEGENDARY: "Legendary",
    Rating.MYTHIC: "Mythic",
}
_LENGTH = {
    Length.TINY: "Tiny",
    Length.SHORT: "Short",
    Length.MEDIUM: "Medium",
    Length.LONG: "Long",
    Length.XL: "XL",
    Length.PLATFORMER: "Platformer",
}
_LEADERBOARD = {
    LeaderboardKind.STARS: "Stars",
    LeaderboardKind.MOONS: "Moons",
    LeaderboardKind.DEMONS: "Demons",
    LeaderboardKind.USER_COINS: "User coins",
    LeaderboardKind.CREATOR_POINTS: "Creator points",
}
_MOD_LEVEL = {
    ModLevel.NONE: "",
    ModLevel.MOD: "Moderator",
    ModLevel.ELDER: "Elder moderator",
    ModLevel.LEADERBOARD: "Leaderboard moderator",
}
_ICON_KIND = {
    IconKind.CUBE: "Cube",
    IconKind.SHIP: "Ship",
    IconKind.BALL: "Ball",
    IconKind.UFO: "UFO",
    IconKind.WAVE: "Wave",
    IconKind.ROBOT: "Robot",
    IconKind.SPIDER: "Spider",
    IconKind.SWING: "Swing",
    IconKind.JETPACK: "Jetpack",
}


def difficulty(value: Difficulty) -> str:
    return _DIFFICULTY[value]


def difficulty_class(value: Difficulty) -> str:
    """A CSS hook: `demon` for every demon tier, else the tier name."""

    if value >= Difficulty.EASY_DEMON:
        return "demon"

    return _DIFFICULTY[value].lower()


def rating(value: Rating) -> str:
    return _RATING[value]


def length(value: Length) -> str:
    return _LENGTH[value]


def leaderboard_kind(value: LeaderboardKind) -> str:
    return _LEADERBOARD[value]


def mod_level(value: ModLevel) -> str:
    return _MOD_LEVEL[value]


def icon_kind(value: IconKind) -> str:
    return _ICON_KIND[value]
