from datetime import UTC, date, datetime, time
from itertools import combinations
from math import isfinite
from typing import Annotated, Literal

import ephemera as eph
from pydantic import BaseModel, Field, model_validator

from app.core.errors import ApiError
from app.readings.bazi import BirthInput, local_birth, solar_date, validate_zone
from app.readings.rules import signs

VERSION = "ephemera-0.4.1-v2"
HOUSES = {
    "placidus": eph.HouseSystem.PLACIDUS,
    "equal": eph.HouseSystem.EQUAL,
    "whole_sign": eph.HouseSystem.WHOLE_SIGN,
}
PLANETS = {
    "SUN": "太阳",
    "MOON": "月亮",
    "MERCURY": "水星",
    "VENUS": "金星",
    "MARS": "火星",
    "JUPITER": "木星",
    "SATURN": "土星",
    "URANUS": "天王星",
    "NEPTUNE": "海王星",
    "PLUTO": "冥王星",
}
EXTRAS = {"CHIRON": "凯龙星", "TRUE_NODE": "北交点"}
ASPECTS = ((0, "合相"), (60, "六合"), (90, "刑相"), (120, "拱相"), (180, "对冲"))
SIGN_IDS = tuple(signs)
MOON_PHASES = ("新月", "蛾眉月", "上弦月", "盈凸月", "满月", "亏凸月", "下弦月", "残月")


class AstroInput(BaseModel):
    birth: BirthInput
    latitude: Annotated[float, Field(gt=-90, lt=90, allow_inf_nan=False)]
    longitude: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
    house_system: Literal["placidus", "equal", "whole_sign"] = "placidus"
    zodiac: Literal["tropical", "sidereal"] = "tropical"
    orb: Annotated[float, Field(ge=1, le=10)] = 6
    extras: bool = False

    @model_validator(mode="after")
    def require_time(self) -> "AstroInput":
        if self.birth.birth_time is None:
            raise ValueError("计算本命盘需要出生时刻。")
        return self


def normalized(value: float) -> float:
    return value % 360


def display_degree(value: float) -> float:
    return normalized(round(value, 6))


def julian_day(clock: datetime) -> float:
    utc = clock.astimezone(UTC)
    fraction = (utc.hour * 3600 + utc.minute * 60 + utc.second + utc.microsecond / 1e6) / 86400
    return eph.julian_date(utc.year, utc.month, utc.day + fraction)


def moon_phase(day: date, timezone: str) -> dict:
    jd = julian_day(datetime.combine(day, time(12), validate_zone(timezone)))
    sun = eph.position(eph.Body.SUN, jd)
    moon = eph.position(eph.Body.MOON, jd)
    if sun is None or moon is None:
        raise ApiError(422, "ephemeris_data_unavailable", "星历缺少此日期的日月数据。")
    elongation = normalized(moon.longitude - sun.longitude)
    return {
        "name": MOON_PHASES[int((elongation + 22.5) // 45) % 8],
        "elongation": display_degree(elongation),
        "timezone": timezone,
        "basis": "local_noon",
    }


def house_for(degree: float, cusps: list[float]) -> int:
    for index, start in enumerate(cusps):
        end = cusps[(index + 1) % len(cusps)]
        if normalized(degree - start) < normalized(end - start):
            return index + 1
    raise ApiError(422, "invalid_house_geometry", "无法确定此地点的宫位。")


def build_astro(payload: AstroInput) -> dict:
    birth = payload.birth
    assert birth.birth_time is not None
    utc = local_birth(
        birth, solar_date(birth), birth.birth_time, validate_zone(birth.timezone)
    ).astimezone(UTC)
    jd = julian_day(utc)

    asc, mc = eph.asc_mc(jd, payload.longitude, payload.latitude)
    if not all(isfinite(value) for value in (asc, mc)):
        raise ApiError(422, "invalid_house_geometry", "该地点无法计算有效的上升点与天顶。")
    sidereal = payload.zodiac == "sidereal"
    offset = eph.ayanamsa_lahiri(eph.ut_to_tt(jd)) if sidereal else 0
    if payload.house_system == "whole_sign":
        first = int(normalized(asc - offset) // 30) * 30
        cusps = [normalized(first + index * 30) for index in range(12)]
    else:
        geometry = eph.houses_info(
            jd, payload.longitude, payload.latitude, HOUSES[payload.house_system]
        )
        if geometry is not None and geometry.fallback:
            raise ApiError(422, "high_latitude_house_system", "高纬度地点请选择等宫制或整宫制。")
        if (
            geometry is None
            or len(geometry.cusps) != 12
            or not all(isfinite(value) for value in geometry.cusps)
        ):
            raise ApiError(422, "invalid_house_geometry", "该地点无法计算所选宫制。")
        cusps = [normalized(item - offset) for item in geometry.cusps]

    positions = []
    definitions = PLANETS | EXTRAS if payload.extras else PLANETS
    for name, planet in definitions.items():
        position = eph.position(getattr(eph.Body, name), jd)
        if position is None or not all(
            isfinite(item) for item in (position.longitude, position.longitude_speed)
        ):
            raise ApiError(422, "ephemeris_data_unavailable", "星历缺少此星体的数据。")
        degree = normalized(position.longitude - offset)
        positions.append(
            {
                "id": name.lower(),
                "name": planet,
                "longitude": degree,
                "speed": round(position.longitude_speed, 6),
                "sign": SIGN_IDS[int(degree // 30)],
                "house": house_for(degree, cusps),
                "retrograde": position.longitude_speed < 0,
            }
        )

    aspects = []
    for first, second in combinations(positions, 2):
        separation = abs((first["longitude"] - second["longitude"] + 180) % 360 - 180)
        exact, label = min(ASPECTS, key=lambda item: abs(separation - item[0]))
        margin = abs(separation - exact)
        if margin <= payload.orb:
            aspects.append(
                {
                    "first": first["id"],
                    "second": second["id"],
                    "name": label,
                    "angle": exact,
                    "orb": round(margin, 4),
                }
            )
    return {
        "house_system": payload.house_system,
        "zodiac": payload.zodiac,
        "ayanamsa": "lahiri" if sidereal else None,
        "ascendant": display_degree(asc - offset),
        "midheaven": display_degree(mc - offset),
        "cusps": [display_degree(item) for item in cusps],
        "planets": [{**item, "longitude": display_degree(item["longitude"])} for item in positions],
        "aspects": aspects,
        "orb": payload.orb,
        "utc": utc.isoformat(),
    }
