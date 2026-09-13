from gdformat.enums import ChestType
from gdformat.enums import DemonDifficulty
from gdformat.enums import Difficulty
from gdformat.enums import Length
from gdformat.enums import MapPackDifficulty
from gdformat.enums import ModLevel
from gdformat.enums import Platform
from gdformat.enums import QuestItem
from gdformat.enums import Rating
from gdformat.enums import RewardItem
from gdformat.enums import SendFeature
from gdformat.enums import TimelyType
from gdformat.enums import Visibility
from poltergeist_core.resources import BanType
from poltergeist_core.resources import LeaderboardKind
from poltergeist_core.resources import ModTarget
from poltergeist_core.resources import SongSource
from poltergeist_core.resources import UserKind

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


_BAN = {
    BanType.ACCOUNT: "Account",
    BanType.COMMENT: "Comment",
    BanType.UPLOAD: "Upload",
    BanType.LEADERBOARD: "Leaderboard",
    BanType.CREATOR: "Creator",
}
_KIND = {UserKind.PLAYER: "Player", UserKind.BOT: "Bot"}
_VISIBILITY = {
    Visibility.PUBLIC: "Public",
    Visibility.FRIENDS: "Friends only",
    Visibility.UNLISTED: "Unlisted",
}
_TIMELY = {
    TimelyType.DAILY: "Daily",
    TimelyType.WEEKLY: "Weekly",
    TimelyType.EVENT: "Event",
}
_MOD_TARGET = {
    ModTarget.USER: "User",
    ModTarget.LEVEL: "Level",
    ModTarget.LEVEL_LIST: "List",
    ModTarget.COMMENT: "Comment",
    ModTarget.ACCOUNT_COMMENT: "Profile post",
    ModTarget.SONG: "Song",
    ModTarget.TIMELY_LEVEL: "Timely",
    ModTarget.MAP_PACK: "Map pack",
    ModTarget.GAUNTLET: "Gauntlet",
    ModTarget.QUEST: "Quest",
    ModTarget.SECRET_REWARD: "Vault code",
    ModTarget.ROLE: "Role",
    ModTarget.SERVER: "Server",
}
_QUEST_ITEM = {
    QuestItem.ORBS: "Orbs",
    QuestItem.COINS: "Coins",
    QuestItem.STARS: "Stars",
}
_CHEST = {
    ChestType.SMALL: "Small chest",
    ChestType.LARGE: "Large chest",
    ChestType.EVENT: "Event chest",
}
_REWARD_ITEM = {
    RewardItem.ORBS: "Orbs",
    RewardItem.DIAMONDS: "Diamonds",
    RewardItem.FIRE_SHARD: "Fire shard",
    RewardItem.ICE_SHARD: "Ice shard",
    RewardItem.POISON_SHARD: "Poison shard",
    RewardItem.SHADOW_SHARD: "Shadow shard",
    RewardItem.LAVA_SHARD: "Lava shard",
    RewardItem.EARTH_SHARD: "Earth shard",
    RewardItem.BLOOD_SHARD: "Blood shard",
    RewardItem.METAL_SHARD: "Metal shard",
    RewardItem.LIGHT_SHARD: "Light shard",
    RewardItem.SOUL_SHARD: "Soul shard",
    RewardItem.DEMON_KEY: "Demon key",
    RewardItem.GOLD_KEY: "Gold key",
}
_MAP_PACK_DIFFICULTY = {
    MapPackDifficulty.AUTO: "Auto",
    MapPackDifficulty.EASY: "Easy",
    MapPackDifficulty.NORMAL: "Normal",
    MapPackDifficulty.HARD: "Hard",
    MapPackDifficulty.HARDER: "Harder",
    MapPackDifficulty.INSANE: "Insane",
    MapPackDifficulty.HARD_DEMON: "Hard Demon",
    MapPackDifficulty.EASY_DEMON: "Easy Demon",
    MapPackDifficulty.MEDIUM_DEMON: "Medium Demon",
    MapPackDifficulty.INSANE_DEMON: "Insane Demon",
    MapPackDifficulty.EXTREME_DEMON: "Extreme Demon",
}
_SEND_FEATURE = {
    SendFeature.STAR: "Rated only",
    SendFeature.FEATURE: "Featured",
    SendFeature.EPIC: "Epic",
    SendFeature.LEGENDARY: "Legendary",
    SendFeature.MYTHIC: "Mythic",
}
_DEMON = {
    DemonDifficulty.EASY: "Easy",
    DemonDifficulty.MEDIUM: "Medium",
    DemonDifficulty.HARD: "Hard",
    DemonDifficulty.INSANE: "Insane",
    DemonDifficulty.EXTREME: "Extreme",
}
_PLATFORM = {
    Platform.UNKNOWN: "Unknown",
    Platform.IOS: "iOS",
    Platform.ANDROID: "Android",
    Platform.WINDOWS: "Windows",
    Platform.MACOS: "macOS",
}
_SONG_SOURCE = {
    SongSource.NEWGROUNDS: "Newgrounds",
    SongSource.LIBRARY: "Library",
    SongSource.CUSTOM: "Custom",
}
_GAUNTLET = {
    1: "Fire",
    2: "Ice",
    3: "Poison",
    4: "Shadow",
    5: "Lava",
    6: "Bonus",
    7: "Chaos",
    8: "Demon",
    9: "Time",
    10: "Crystal",
    11: "Magic",
    12: "Spike",
    13: "Monster",
    14: "Doom",
    15: "Death",
    16: "Forest",
    17: "Rune",
    18: "Force",
    19: "Spooky",
    20: "Dragon",
    21: "Water",
    22: "Haunted",
    23: "Acid",
    24: "Witch",
    25: "Power",
    26: "Potion",
    27: "Snake",
    28: "Toxic",
    29: "Halloween",
    30: "Treasure",
    31: "Ghost",
    32: "Spider",
    33: "Gem",
    34: "Inferno",
    35: "Portal",
    36: "Strange",
    37: "Fantasy",
    38: "Christmas",
    39: "Surprise",
    40: "Mystery",
    41: "Cursed",
    42: "Cyborg",
    43: "Castle",
    44: "Grave",
    45: "Temple",
    46: "World",
    47: "Galaxy",
    48: "Universe",
    49: "Discord",
    50: "Split",
    51: "NCS I",
    52: "NCS II",
}


def ban_type(value: BanType) -> str:
    return _BAN[value]


def user_kind(value: UserKind) -> str:
    return _KIND[value]


def visibility(value: Visibility) -> str:
    return _VISIBILITY[value]


def timely_type(value: TimelyType) -> str:
    return _TIMELY[value]


def mod_target(value: ModTarget) -> str:
    return _MOD_TARGET[value]


def quest_item(value: QuestItem) -> str:
    return _QUEST_ITEM[value]


def chest_type(value: ChestType) -> str:
    return _CHEST[value]


def reward_item(value: RewardItem) -> str:
    """Items outside the curated set (icon unlocks) read as their enum name."""

    return _REWARD_ITEM.get(value, value.name.replace("_", " ").capitalize())


def map_pack_difficulty(value: MapPackDifficulty) -> str:
    return _MAP_PACK_DIFFICULTY[value]


def send_feature(value: SendFeature) -> str:
    return _SEND_FEATURE[value]


def demon_difficulty(value: DemonDifficulty) -> str:
    return _DEMON[value]


def platform(value: Platform) -> str:
    return _PLATFORM[value]


def song_source(value: SongSource) -> str:
    return _SONG_SOURCE[value]


def gauntlet(gauntlet_id: int) -> str:
    return _GAUNTLET.get(gauntlet_id, f"Gauntlet {gauntlet_id}")
