from collections import Counter
from datetime import UTC, date, datetime, time
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lunar_python import EightChar, Lunar, LunarYear, Solar
from lunar_python.util import LunarUtil
from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError

BAZI_VERSION = "bazi-civil-2"
CHINA = ZoneInfo("Asia/Shanghai")
GROWTH_START = dict(zip(LunarUtil.GAN[1:], "亥午寅酉寅酉巳子申卯", strict=True))
ELEMENTS = ("木", "火", "土", "金", "水")


def validate_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise ValueError("请输入有效的 IANA 时区。") from error


class BirthInput(BaseModel):
    calendar: Literal["solar", "lunar"] = "solar"
    year: Annotated[int, Field(ge=1901, le=2099)]
    month: Annotated[int, Field(ge=1, le=12)]
    day: Annotated[int, Field(ge=1, le=31)]
    birth_time: time | None = None
    timezone: Annotated[str, Field(max_length=64)] = "Asia/Shanghai"
    leap_month: bool = False
    fold: Literal[0, 1] | None = None

    @model_validator(mode="after")
    def validate_birth(self) -> "BirthInput":
        if self.leap_month and self.calendar != "lunar":
            raise ValueError("闰月仅适用于农历。")
        day = solar_date(self)
        zone = validate_zone(self.timezone)
        if self.birth_time is not None:
            if self.birth_time.tzinfo is not None:
                raise ValueError("出生时间使用当地钟表时间，时区请单独提供。")
            local_birth(self, day, self.birth_time, zone)
        return self


def solar_date(birth: BirthInput) -> date:
    if birth.calendar == "solar":
        return date(birth.year, birth.month, birth.day)
    month = -birth.month if birth.leap_month else birth.month
    lunar_month = LunarYear.fromYear(birth.year).getMonth(month)
    if lunar_month is None or birth.day > lunar_month.getDayCount():
        raise PydanticCustomError("invalid_lunar_birth", "所选农历日期或闰月无效。")
    solar = Lunar.fromYmd(birth.year, month, birth.day).getSolar()
    return date(solar.getYear(), solar.getMonth(), solar.getDay())


def local_birth(birth: BirthInput, day: date, clock: time, zone: ZoneInfo) -> datetime:
    naive = datetime.combine(day, clock)
    candidates = [naive.replace(tzinfo=zone, fold=choice) for choice in (0, 1)]
    valid = [
        item
        for item in candidates
        if item.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == naive
    ]
    if not valid:
        raise PydanticCustomError("skipped_birth_time", "所选出生时间落在夏令时跳过的区间。")
    if len(valid) == 2 and valid[0].utcoffset() != valid[1].utcoffset() and birth.fold is None:
        raise PydanticCustomError(
            "repeated_birth_time", "所选出生时间出现两次，请选择第一次或第二次。"
        )
    return next((item for item in valid if item.fold == birth.fold), valid[0])


def eight_char(clock: datetime):
    chart = (
        Solar.fromYmdHms(clock.year, clock.month, clock.day, clock.hour, clock.minute, clock.second)
        .getLunar()
        .getEightChar()
    )
    chart.setSect(2)
    return chart


def pillar(ganzhi: str, day_stem: str | None, *, day: bool = False) -> dict:
    stem, branch = ganzhi
    hidden_stems = LunarUtil.ZHI_HIDE_GAN[branch]
    stage = None
    if day_stem is not None:
        forward = (LunarUtil.GAN.index(day_stem) - 1) % 2 == 0
        distance = LunarUtil.ZHI.index(branch) - LunarUtil.ZHI.index(GROWTH_START[day_stem])
        stage = EightChar.CHANG_SHENG[(distance if forward else -distance) % 12]
    return {
        "ganzhi": ganzhi,
        "elements": LunarUtil.WU_XING_GAN[stem] + LunarUtil.WU_XING_ZHI[branch],
        "hidden_stems": hidden_stems,
        "stem_ten_god": (
            ("日主" if day else LunarUtil.SHI_SHEN[day_stem + stem]) if day_stem else None
        ),
        "branch_ten_gods": [LunarUtil.SHI_SHEN[day_stem + hidden] for hidden in hidden_stems]
        if day_stem
        else None,
        "nayin": LunarUtil.NAYIN[ganzhi],
        "void": LunarUtil.getXunKong(ganzhi),
        "growth_stage": stage,
    }


def build_bazi(birth: BirthInput, *, late_zi: bool = False) -> dict:
    day = solar_date(birth)
    zone = validate_zone(birth.timezone)
    known = birth.birth_time is not None
    local_clock = (
        local_birth(birth, day, birth.birth_time, zone)
        if birth.birth_time is not None
        else datetime.combine(day, time(12), zone)
    )
    local_chart = eight_char(local_clock)
    if late_zi and known:
        local_chart.setSect(1)
    solar_terms_chart = eight_char(local_clock.astimezone(CHINA))
    day_pillar = local_chart.getDay() if known or not late_zi else None
    day_stem = day_pillar[0] if day_pillar else None

    # The selected day boundary also controls the Five Rats hour stem.
    hour_pillar = None
    if known and day_stem is not None:
        branch = local_chart.getTimeZhi()
        day_index = LunarUtil.GAN.index(day_stem) - 1
        branch_index = LunarUtil.ZHI.index(branch) - 1
        hour_pillar = LunarUtil.GAN[(day_index % 5 * 2 + branch_index) % 10 + 1] + branch

    ganzhi = {
        "year": solar_terms_chart.getYear(),
        "month": solar_terms_chart.getMonth(),
        "day": day_pillar,
        "hour": hour_pillar,
    }
    if not known:
        start = eight_char(datetime.combine(day, time.min, zone).astimezone(CHINA))
        end = eight_char(datetime.combine(day, time.max, zone).astimezone(CHINA))
        for name in ("year", "month"):
            getter = "get" + name.capitalize()
            if getattr(start, getter)() != getattr(end, getter)():
                ganzhi[name] = None

    chart = {
        name: pillar(value, day_stem, day=name == "day") if value else None
        for name, value in ganzhi.items()
    }
    counts = Counter(element for item in chart.values() if item for element in item["elements"])
    return {
        "solar_date": day.isoformat(),
        "timezone": birth.timezone,
        "time_known": birth.birth_time is not None,
        "solar_term_basis": "Asia/Shanghai",
        "day_boundary": "local_23" if late_zi else "local_midnight",
        "pillars": chart,
        "day_master": day_stem,
        "elements": {element: counts[element] for element in ELEMENTS},
    }
