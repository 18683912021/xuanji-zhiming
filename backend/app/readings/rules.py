import json
import secrets
from datetime import date
from pathlib import Path
from random import SystemRandom

from lunar_python import Solar

from app.core.errors import ApiError

with Path(__file__).with_name("catalog.json").open(encoding="utf-8") as file:
    catalog = json.load(file)

CATALOG_VERSION = catalog["version"]
signs = {sign["id"]: sign for sign in catalog["signs"]}
spreads = {spread["id"]: spread for spread in catalog["spreads"]}
cards = catalog["cards"]
DICE_PLANETS = (
    "太阳",
    "月亮",
    "水星",
    "金星",
    "火星",
    "木星",
    "土星",
    "天王星",
    "海王星",
    "冥王星",
)
BOOK_PAGES = (
    "今天先做一件可逆的小事。",
    "从对方的角度重新说一遍。",
    "让问题具体到一个日期。",
    "给自己一天重新观察。",
    "先问一个真正想知道的问题。",
    "把手上已有的线索列出来。",
    "暂时留一个备选方案。",
    "记下什么会让你改变主意。",
)

TRIGRAMS = ("111", "110", "101", "100", "011", "010", "001", "000")
HEXAGRAMS = (
    ("乾", "履", "同人", "无妄", "姤", "讼", "遁", "否"),
    ("夬", "兑", "革", "随", "大过", "困", "咸", "萃"),
    ("大有", "睽", "离", "噬嗑", "鼎", "未济", "旅", "晋"),
    ("大壮", "归妹", "丰", "震", "恒", "解", "小过", "豫"),
    ("小畜", "中孚", "家人", "益", "巽", "涣", "渐", "观"),
    ("需", "节", "既济", "屯", "井", "坎", "蹇", "比"),
    ("大畜", "损", "贲", "颐", "蛊", "蒙", "艮", "剥"),
    ("泰", "临", "明夷", "复", "升", "师", "谦", "坤"),
)
YAO_LABELS = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}
YAO_NAMES = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")


def zodiac(sign_id: str) -> dict:
    sign = signs.get(sign_id)
    if sign is None:
        raise ApiError(404, "sign_not_found", "星座不存在。")
    return sign


def draw_tarot(spread_id: str, positions: list[int] | None = None) -> dict:
    spread = spreads[spread_id]
    deck = SystemRandom().sample(range(len(cards)), 6)
    indexes = [deck[index] for index in positions] if positions is not None else deck
    indexes = indexes[: len(spread["positions"])]
    result = []
    for index, position in zip(indexes, spread["positions"], strict=True):
        name, upright, reversed_text = cards[index]
        reversed_ = bool(secrets.randbelow(2))
        result.append(
            {
                "index": index,
                "name": name,
                "position": position,
                "reversed": reversed_,
                "meaning": reversed_text if reversed_ else upright,
            }
        )
    return {"spread": spread, "cards": result}


def draw_oracle() -> dict:
    index = secrets.randbelow(len(catalog["verses"]))
    return {"index": index, **catalog["verses"][index], "source": "玄机知命原创签文"}


def roll_dice() -> dict:
    planet = secrets.randbelow(len(DICE_PLANETS))
    sign = secrets.choice(tuple(signs))
    return {
        "planet_index": planet,
        "planet": DICE_PLANETS[planet],
        "sign": sign,
        "sign_name": signs[sign]["name"],
        "house": secrets.randbelow(12) + 1,
    }


def open_book(previous_answer: str | None = None) -> dict:
    return {"answer": secrets.choice([page for page in BOOK_PAGES if page != previous_answer])}


def hexagram(lines: list[int]) -> str:
    lower = "".join(str(value % 2) for value in lines[:3])
    upper = "".join(str(value % 2) for value in lines[3:])
    return HEXAGRAMS[TRIGRAMS.index(upper)][TRIGRAMS.index(lower)]


def cast_liuyao(lines: list[int] | None) -> dict:
    coins = (
        None
        if lines is not None
        else [[secrets.choice((2, 3)) for _ in range(3)] for _ in range(6)]
    )
    values = lines if lines is not None else [sum(group) for group in coins]
    moving = [index for index, value in enumerate(values, start=1) if value in (6, 9)]
    changed = [{6: 7, 9: 8}.get(value, value) for value in values]
    return {
        "lines": [
            {
                "number": index,
                "name": YAO_NAMES[index - 1],
                "value": value,
                "label": YAO_LABELS[value],
            }
            for index, value in enumerate(values, start=1)
        ],
        "coins": coins,
        "hexagram": hexagram(values),
        "changed_hexagram": hexagram(changed) if moving else None,
        "moving_lines": moving,
    }


def calendar_day(day: date) -> dict:
    lunar = Solar.fromYmd(day.year, day.month, day.day).getLunar()
    return {
        "date": day.isoformat(),
        "lunar": {
            "year": lunar.getYear(),
            "month": abs(lunar.getMonth()),
            "day": lunar.getDay(),
            "leap_month": lunar.getMonth() < 0,
            "label": lunar.getMonthInChinese() + "月" + lunar.getDayInChinese(),
        },
        "solar_term": lunar.getJieQi() or None,
        "festivals": lunar.getFestivals(),
    }
