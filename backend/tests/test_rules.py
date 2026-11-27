from datetime import date
from itertools import product

import pytest
from pydantic import ValidationError

from app.readings.bazi import BirthInput, build_bazi
from app.readings.rules import calendar_day, cast_liuyao, draw_tarot, hexagram, spreads


@pytest.mark.parametrize("spread_id", list(spreads))
def test_tarot_spread_has_ordered_unique_cards(spread_id):
    expected = spreads[spread_id]["positions"]
    cards = draw_tarot(spread_id, list(range(len(expected))))["cards"]
    assert [card["position"] for card in cards] == expected
    assert len({card["index"] for card in cards}) == len(expected)
    assert all(0 <= card["index"] < 78 and card["meaning"] for card in cards)


def test_liuyao_preserves_bottom_first_order_and_static_hexagram():
    static = cast_liuyao([7, 7, 7, 7, 7, 7])
    assert static["hexagram"] == "乾"
    assert static["changed_hexagram"] is None
    moving = cast_liuyao([9, 7, 7, 7, 7, 7])
    assert moving["changed_hexagram"] == "姤"
    assert moving["moving_lines"] == [1]
    assert len({hexagram(list(lines)) for lines in product((7, 8), repeat=6)}) == 64
    tossed = cast_liuyao(None)
    assert [sum(group) for group in tossed["coins"]] == [line["value"] for line in tossed["lines"]]


def test_bazi_reference_and_unknown_time():
    birth = BirthInput(year=2022, month=8, day=28, birth_time="01:50")
    chart = build_bazi(birth)
    assert [pillar["ganzhi"] for pillar in chart["pillars"].values()] == [
        "壬寅",
        "戊申",
        "癸丑",
        "癸丑",
    ]
    unknown = build_bazi(BirthInput(year=2022, month=8, day=28))
    assert unknown["pillars"]["hour"] is None
    assert sum(unknown["elements"].values()) == 6


def test_bazi_solar_term_crossover_does_not_assume_noon():
    early = build_bazi(BirthInput(year=2024, month=2, day=4, birth_time="08:00"))
    late = build_bazi(BirthInput(year=2024, month=2, day=4, birth_time="22:00"))
    unknown = build_bazi(BirthInput(year=2024, month=2, day=4))
    assert early["pillars"]["year"]["ganzhi"] != late["pillars"]["year"]["ganzhi"]
    assert unknown["pillars"]["year"] is None
    assert unknown["pillars"]["month"] is None


def test_bazi_day_and_hour_share_the_selected_zi_boundary():
    birth = BirthInput(year=2022, month=8, day=28, birth_time="23:30")
    civil = build_bazi(birth)["pillars"]
    late_zi = build_bazi(birth, late_zi=True)["pillars"]
    next_day = build_bazi(BirthInput(year=2022, month=8, day=29, birth_time="00:00"))["pillars"]
    assert [civil[part]["ganzhi"] for part in ("day", "hour")] == ["癸丑", "壬子"]
    assert late_zi["day"] == next_day["day"]
    assert late_zi["hour"] == next_day["hour"]
    assert late_zi["hour"]["growth_stage"] == "沐浴"
    unknown = build_bazi(BirthInput(year=2022, month=8, day=28), late_zi=True)
    assert unknown["day_master"] is None
    assert unknown["pillars"]["year"]["stem_ten_god"] is None
    assert unknown["pillars"]["month"]["growth_stage"] is None


def test_lunar_leap_month_and_clock_fold():
    from app.readings.astro import AstroInput, build_astro

    leap = BirthInput(year=2020, month=4, day=1, calendar="lunar", leap_month=True)
    assert build_bazi(leap)["solar_date"] == "2020-05-23"
    fields = dict(year=2024, month=11, day=3, birth_time="01:30", timezone="America/New_York")
    with pytest.raises(ValidationError, match="出现两次"):
        BirthInput(**fields)
    for fold, expected in ((0, "2024-11-03T05:30:00+00:00"), (1, "2024-11-03T06:30:00+00:00")):
        birth = BirthInput(**fields, fold=fold)
        chart = build_astro(AstroInput(birth=birth, latitude=40.7, longitude=-74.0))
        assert chart["utc"] == expected


@pytest.mark.parametrize(
    ("day", "expected", "angle"),
    [
        (date(2024, 4, 8), "新月", 0),
        (date(2024, 4, 15), "上弦月", 90),
        (date(2024, 4, 23), "满月", 180),
        (date(2024, 5, 1), "下弦月", 270),
    ],
)
def test_moon_phase_against_2024_principal_phase_dates(day, expected, angle):
    from app.readings.astro import moon_phase

    phase = moon_phase(day, "America/New_York")
    assert phase["name"] == expected
    assert 0 <= phase["elongation"] < 360
    assert abs((phase["elongation"] - angle + 180) % 360 - 180) < 6


@pytest.mark.parametrize(
    "fields",
    [
        {"calendar": "lunar", "year": 2025, "month": 3, "day": 1, "leap_month": True},
        {"year": 2024, "month": 2, "day": 30},
        {
            "year": 2024,
            "month": 3,
            "day": 10,
            "birth_time": "02:30",
            "timezone": "America/New_York",
        },
    ],
)
def test_invalid_birth_input(fields):
    with pytest.raises(ValidationError):
        BirthInput(**fields)


def test_calendar_lunar_new_year():
    result = calendar_day(date(2024, 2, 10))
    assert (result["lunar"]["month"], result["lunar"]["day"]) == (1, 1)
    assert "春节" in result["festivals"]


def test_natal_calculation_uses_real_positions_cusps_and_timezone():
    from app.readings.astro import AstroInput, build_astro

    birth = BirthInput(year=2000, month=1, day=1, birth_time="12:00", timezone="Europe/London")
    query = AstroInput(birth=birth, latitude=51.5074, longitude=-0.1278)
    chart = build_astro(query)
    moon = next(body for body in chart["planets"] if body["id"] == "moon")
    assert moon["longitude"] == pytest.approx(223.323735, abs=0.001)
    assert chart["ascendant"] == pytest.approx(24.014589, abs=0.001)
    assert len(chart["cusps"]) == 12
    assert all(1 <= body["house"] <= 12 for body in chart["planets"])
    assert all(item["orb"] <= query.orb for item in chart["aspects"])

    sidereal = build_astro(
        query.model_copy(update={"zodiac": "sidereal", "house_system": "whole_sign"})
    )
    assert sidereal["ayanamsa"] == "lahiri"
    assert all(cusp % 30 == 0 for cusp in sidereal["cusps"])
    assert sidereal["planets"][1]["longitude"] != moon["longitude"]


def test_placidus_high_latitude_requires_explicit_house_change():
    from app.core.errors import ApiError
    from app.readings.astro import AstroInput, build_astro

    birth = BirthInput(year=2000, month=1, day=1, birth_time="12:00")
    with pytest.raises(ApiError, match="请选择等宫制或整宫制"):
        build_astro(AstroInput(birth=birth, latitude=69.6, longitude=18.9))
