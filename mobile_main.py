"""
consolidated_birthchart_generator.py
----------------------------------------------
Goal: Collect global birth data (POB anywhere in the world), compute sidereal basics
(Julian Day, Ayanamsa, planetary positions), Panchanga, and now Nakshatra–pāda transitions.
Populate into base_dict and feed to PPTX generator.
"""

import pandas as pd
import swisseph as swe
import datetime as dt
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Pt
import math
import requests
import pytz
import traceback
import inspect
import calendar

#ist_tz = timezone(timedelta(hours=5, minutes=30))


SHOW_FINAL_OUTPUT = True   # set False to suppress even the final print

# --- Panchanga constants ---
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada (Krishna)", "Dwitiya (Krishna)", "Tritiya (Krishna)", "Chaturthi (Krishna)",
    "Panchami (Krishna)", "Shashti (Krishna)", "Saptami (Krishna)", "Ashtami (Krishna)",
    "Navami (Krishna)", "Dashami (Krishna)", "Ekadashi (Krishna)", "Dwadashi (Krishna)",
    "Trayodashi (Krishna)", "Chaturdashi (Krishna)", "Amavasya"
]

NAKSHATRA_NAMES = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
    "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha",
    "Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta",
    "Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

YOGA_NAMES = [
    "Vishkumbha","Preeti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma","Dhriti",
    "Shoola","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra","Siddhi","Vyatipata",
    "Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"
]

KARANA_NAMES = [
    "Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti",
    "Shakuni","Chatushpada","Nagava","Kimstughna"
]

KARANA_SEQUENCE = (
    ["Kimstughna"]
    + ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"] * 8
    + ["Shakuni", "Chatushpada", "Naga"]
)
planet_map = {
                "Sun": "Su", "Moon": "Mo", "Mercury": "Me", "Venus": "Ve",
                "Mars": "Ma", "Jupiter": "Ju", "Saturn": "Sa",
                "Rahu": "Ra", "Ketu": "Ke", "Ascendant": "Asc"
}

WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# Set ephemeris path
swe.set_ephe_path("C:/Users/murth/Downloads/Swisseph_extractions_13Nov25/ephe")

# Planets we compute

# Explicit mapping from Swisseph planet constants to our base_dict keys
PLANET_KEYS = {
    swe.SUN:     "SUN",
    swe.MOON:    "MOON",
    swe.MARS:    "MAR",
    swe.MERCURY: "MER",
    swe.JUPITER: "JUP",
    swe.VENUS:   "VEN",
    swe.SATURN:  "SAT",
}

TELUGU_YEAR_NAMES = [
    "Prabhava", "Vibhava", "Śukla", "Pramōdyuta", "Prajōtpatti", "Āṅgīrasa", "Śrīmukha", "Bhava",
    "Yuva", "Dhāta", "Īśvara", "Bahudhānya", "Pramādhi", "Vikrama", "Vr̥ṣa", "Citrabhānu",
    "Svabhānu", "Tāraṇa", "Pārthiva", "Vyaya", "Sarvajittu", "Sarvadhāri", "Virōdhi", "Vikr̥ti",
    "Khara", "Nandana", "Vijaya", "Jaya", "Manmadha", "Durmukhi", "Hēvaḷambi", "Viḷambi",
    "Vikāri", "Śārvari", "Plava", "Śubhakr̥ttu", "Śōbhakr̥ttu", "Krōdhi", "Viśvāvasu", "Parābhava",
    "Plavaṅga", "Kīlaka", "Saumya", "Sādhāraṇa", "Virōdhikr̥ttu", "Paridhāvi", "Pramādīca", "Ānanda",
    "Rākṣasa", "Nala", "Piṅgaḷa", "Kāḷayukti", "Siddhārthi", "Raudri", "Durmati", "Dundubhi",
    "Rudhirōdgāri", "Raktākṣi", "Krōdhana", "Akṣaya"
]
PLANETS = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,   # North Node
        "Ketu": swe.TRUE_NODE    # South Node (can also compute as 180° opposite Rahu)
}

PLANET_LIST = [ swe.SUN, swe.MOON, swe.MARS, swe.MERCURY, swe.JUPITER, swe.VENUS, swe.SATURN, swe.MEAN_NODE, swe.TRUE_NODE ]

PLANET_NAMES = {
    swe.SUN: "Sun",
    swe.MOON: "Moon",
    swe.MARS: "Mars",
    swe.MERCURY: "Mercury",
    swe.JUPITER: "Jupiter",
    swe.VENUS: "Venus",
    swe.SATURN: "Saturn",
    swe.MEAN_NODE: "Rahu",
    swe.TRUE_NODE: "Ketu"
}

swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL

SEFLG_SWIEPH = 2
SEFLG_SIDEREAL = 65536
SE_FLAGS_DEFAULT = SEFLG_SWIEPH | SEFLG_SIDEREAL

# --- Nakshatra pāda transitions helpers ---
NAK = 360.0 / 27.0
PADA = NAK / 4.0

ZODIAC = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]

# Example TITHI_NAMES list (index 0–29)
TITHI_NAMES = [
    "Shukla Prathama", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi", "Shukla Panchami",
    "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami", "Shukla Navami", "Shukla Dashami",
    "Shukla Ekadashi", "Shukla Dwadashi", "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Prathama", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi", "Krishna Panchami",
    "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami", "Krishna Navami", "Krishna Dashami",
    "Krishna Ekadashi", "Krishna Dwadashi", "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"
]

import datetime   # <-- keep this at the top

from datetime import date   # <-- make sure this is at the top of your file

WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# Uses your WEEKDAY_NAMES declaration
# WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

import calendar
import datetime

WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def compute_weekday(year: int, month: int, day: int) -> str:
    """
    Return the weekday name for the given date using calendar.weekday().
    """
    try:
        weekday_index = calendar.weekday(year, month, day)  # 0 = Monday, 6 = Sunday
        return WEEKDAY_NAMES[weekday_index]
    except Exception as e:
        return f"Error computing weekday: {e}"

def get_sunrise_sunset(city_name, dt_obj, tz_string):
    lat, lon, utc_offset, tz_string = lookup_city(city_name)

    # Convert datetime to Julian Day
    jd_ut = swe.julday(
        dt_obj.year,
        dt_obj.month,
        dt_obj.day,
        dt_obj.hour + dt_obj.minute/60.0 + dt_obj.second/3600.0,
        swe.GREG_CAL
    )

    # Compute sunrise and sunset in UTC
    sunrise_utc = swe.rise_trans(jd_ut, swe.SUN, lon, lat, rsmi=swe.CALC_RISE)[1][0]
    sunset_utc  = swe.rise_trans(jd_ut, swe.SUN, lon, lat, rsmi=swe.CALC_SET)[1][0]

    # Apply offset
    offset = tz_to_offset(
        tz_string,
        dt_obj.strftime("%Y-%m-%d"),
        dt_obj.strftime("%H:%M:%S")
    )
    sunrise_local = sunrise_utc + timedelta(hours=offset)
    sunset_local  = sunset_utc + timedelta(hours=offset)

    return sunrise_local, sunset_local



    # Step 4: get precise offset using tz_to_offset()
    #offset = tz_to_offset(tz_string, dob.strftime("%Y-%m-%d"), tob.strftime("%H:%M:%S"))

    # Step 5: apply offset
    sunrise_local = sunrise_utc + timedelta(hours=offset)
    sunset_local  = sunset_utc + timedelta(hours=offset)

    return sunrise_local, sunset_local

def sign_name_from_abs(abs_deg: float) -> str:
    try:
        signs = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
        idx = int(abs_deg // 30) % 12
        return signs[idx]
    except Exception as e:
        print("Error inside sign_name_from_abs, abs_deg =", abs_deg)
        traceback.print_exc()
        raise   # re‑raise so the error still propagates

def ensure_float(x, label="value"):
    if isinstance(x, tuple):
        raise TypeError(f"{label} is tuple; expected float. Got: {x}")
    try:
        return float(x)
    except Exception as e:
        raise TypeError(f"Cannot convert {label} to float; got {type(x)} with value {x}") from e
    
def deg_to_dms(deg: float) -> tuple[int, int, float]:
    d = int(deg)
    m_float = (deg - d) * 60.0
    m = int(m_float)
    s = (m_float - m) * 60.0
    return d, m, s

def format_dms(abs_deg):
    try:
        # 1) Log caller chain for precise identification
        stack = inspect.stack()
        caller = stack[1].function if len(stack) > 1 else "<unknown>"
        grand_caller = stack[2].function if len(stack) > 2 else "<unknown>"
        print(f"[format_dms] called by: {caller} <- {grand_caller}; type={type(abs_deg)} value={abs_deg}")

        # 2) Temporary auto-fix: if a tuple sneaks in, take its first element
        if isinstance(abs_deg, tuple):
            print(f"[format_dms] WARNING: tuple received; using first element. Caller={caller}")
            abs_deg = abs_deg[0]

        # 3) Enforce numeric type
        if not isinstance(abs_deg, (int, float)):
            raise TypeError(f"format_dms expected float, got {type(abs_deg)}")

        in_sign = abs_deg % 30.0
        d = int(in_sign)
        m = int((in_sign - d) * 60)
        s = ((in_sign - d) * 60 - m) * 60
        return f"{d}°{m:02d}'{s:05.2f}\""

    except Exception as e:
        print("Error inside format_dms, abs_deg =", abs_deg)
        traceback.print_exc()
        raise

def get_tithi_transitions(year, month, day, hour, minute, second, utc_offset, steps=24):
    """Compute Tithi transitions for the given day."""
    jd_start = swe.julday(year, month, day, hour + minute/60 + second/3600)
    transitions = []
    for i in range(steps):
        jd = jd_start + i/24.0  # step in hours
        moon_lon = swe.calc_ut(jd, swe.MOON)[0][0]
        sun_lon  = swe.calc_ut(jd, swe.SUN)[0][0]
        ayanamsa = swe.get_ayanamsa(jd)
        moon_sid = (moon_lon - ayanamsa) % 360
        sun_sid  = (sun_lon - ayanamsa) % 360
        sep = (moon_sid - sun_sid) % 360
        tithi_index = int(sep // 12) % len(TITHI_NAMES)
        tithi_name  = TITHI_NAMES[tithi_index]
        dt = swe.revjul(jd, swe.GREG_CAL)
        dt_obj = datetime(dt[0], dt[1], dt[2], int((dt[3])%24), int((dt[3]%1)*60))
        transitions.append({"tithi": tithi_name, "datetime": dt_obj})
    return transitions

def compute_tithi(moon_sidereal, sun_sidereal, year, month, day, hour, minute, second, utc_offset):
    # Current tithi name
    tithi_angle = (moon_sidereal - sun_sidereal) % 360
    tithi_index = int(tithi_angle // 12)
    tithi_name = TITHI_NAMES[tithi_index]

    # Use transitions to find end time and next tithi
    transitions = get_tithi_transitions(year, month, day, hour, minute, second, utc_offset)
    # Find the first transition where tithi changes
    current = None
    next_tithi_name = None
    tithi_end_time = None
    for i in range(1, len(transitions)):
        if transitions[i]["tithi"] != transitions[i-1]["tithi"]:
            current = transitions[i-1]["tithi"]
            next_tithi_name = transitions[i]["tithi"]
            tithi_end_time = transitions[i]["datetime"]
            break

    # Build message
    if tithi_end_time and next_tithi_name:
        tithi_end_message = f"{tithi_name} ends at {tithi_end_time.strftime('%Y-%m-%d %H:%M')}, then {next_tithi_name} begins"
    else:
        tithi_end_message = f"{tithi_name} continues all day"

    return tithi_name, tithi_end_time, next_tithi_name, tithi_end_message

def tz_to_offset(tz_string, dob, tob):
    year, month, day = map(int, dob.split("-"))
    hour, minute, second = map(int, tob.split(":"))
    dt_obj = dt.datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(tz_string))
    offset = dt_obj.utcoffset().total_seconds() / 3600.0


    return offset

def get_all_positions(jd_ut, lat, lon, flags):
    """
    Compute sidereal positions for all planets + Ascendant.
    Returns a list of dicts with keys: name, lon, abs_lon, sign.
    """
    positions = []

    # Planets
    for planet, key in zip(PLANETS, PLANET_KEYS):
        lon, lat_p, dist, speed = swe.calc_ut(jd_ut, planet, flags)
        abs_lon = lon % 360
        sign = SIGNS[int(abs_lon // 30)]
        positions.append({
            "name": key,
            "lon": lon,
            "abs_lon": abs_lon,
            "sign": sign
        })

    # Ascendant (Lagna)
    houses = swe.houses(jd_ut, lat, lon, b'A')  # Placidus system by default
    asc_lon = houses[1][0] % 360                # Ascendant longitude
    asc_sign = SIGNS[int(asc_lon // 30)]
    positions.append({
        "name": "Ascendant",
        "lon": asc_lon,
        "abs_lon": asc_lon,
        "sign": asc_sign
    })

    return positions

def get_sidereal_positions(jd_ut, flags=None, lat=None, lon=None):
    if flags is None:
        flags = SE_FLAGS_DEFAULT

    positions = {}

    # Sidereal mode: Lahiri
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    flags = int(flags) | SEFLG_SIDEREAL

    # Planets
    for planet in PLANET_LIST:
        result = swe.calc_ut(jd_ut, planet, flags)
        lon_val = result[0]
        if isinstance(lon_val, tuple):
            lon_val = lon_val[0]
        lon_val = float(lon_val) % 360.0

        # Rahu/Ketu special case
        if planet == swe.MEAN_NODE:
            positions["Rahu"] = {
                "LONG": format_dms(lon_val),
                "ABS": round(lon_val, 4),
                "SIGN": sign_name_from_abs(lon_val),
            }
            ketu_lon = (lon_val + 180.0) % 360.0
            positions["Ketu"] = {
                "LONG": format_dms(ketu_lon),
                "ABS": round(ketu_lon, 4),
                "SIGN": sign_name_from_abs(ketu_lon),
            }
            continue

        positions[PLANET_NAMES[planet]] = {
            "LONG": format_dms(lon_val),
            "ABS": round(lon_val, 4),
            "SIGN": sign_name_from_abs(lon_val),
        }

    # Ascendant
    if lat is not None and lon is not None:
        houses = swe.houses(jd_ut, lat, lon, b'A')
        asc_lon = float(houses[1][0]) % 360.0
        positions["Ascendant"] = {
            "LONG": format_dms(asc_lon),
            "ABS": round(asc_lon, 4),
            "SIGN": sign_name_from_abs(asc_lon),
        }

    return positions

def compute_julian_day(dob, tob, utc_offset):
    year, month, day = map(int, dob.split("-"))

    parts = tob.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    second = int(parts[2]) if len(parts) > 2 else 0

    utc_offset = float(utc_offset)

    # Compute Julian Day at local civil time
    local_hour = hour + minute / 60.0 + second / 3600.0
    jd_local = swe.julday(year, month, day, local_hour, swe.GREG_CAL)

    # Convert to UT (subtract offset in days)
    jd_ut = jd_local - (utc_offset / 24.0)
    return jd_ut

def get_telugu_year(gregorian_year):
    base_year = 1927  # Prabhava
    index = (gregorian_year - base_year) % 60
    return TELUGU_YEAR_NAMES[index]

def compute_nakshatra(abs_lon, jd_ut, utc_offset):
    nak_index = int(abs_lon // (360/27))   # which Nakshatra
    nak_name = NAKSHATRA_NAMES[nak_index]
    pada_idx = int((abs_lon % (360/27)) // (360/108)) + 1
    nak_full = f"{nak_name} ({pada_idx})"

    jd_temp = jd_ut
    nak_end = None
    while True:
        jd_temp += 0.01  # step ~15 minutes
        moon_pos, _ = swe.calc_ut(jd_temp, swe.MOON, flags)
        ayanamsa = swe.get_ayanamsa(jd_temp)
        moon_sid = (moon_pos[0] - ayanamsa) % 360

        new_nak_index = int(moon_sid // (360/27))
        new_pada_idx = int((moon_sid % (360/27)) // (360/108)) + 1

        if new_nak_index != nak_index or new_pada_idx != pada_idx:
            year, month, day, hour_float = swe.revjul(jd_temp, swe.GREG_CAL)
            hour = int(hour_float)
            minute = int((hour_float % 1) * 60)
            nak_end = dt.datetime(year, month, day, hour, minute)
            break

    return nak_name, pada_idx, nak_end

def compute_karana(moon_sidereal, sun_sidereal):
    tithi_angle = (moon_sidereal - sun_sidereal) % 360
    karana_index = int(tithi_angle // 6)

    # KARANA_SEQUENCE = (
    #     ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"] * 8
    #     + ["Shakuni", "Chatushpada", "Naga", "Kimstughna"]
    # )
    
    KARANA_SEQUENCE = (
    ["Kimstughna"]
    + ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"] * 8
    + ["Shakuni", "Chatushpada", "Naga"]
    )

    karana = KARANA_SEQUENCE[karana_index]

    # 🧾 Debug prints
    # print("\n🔍 Karana Debug")
    # print(f"🌙 Moon sidereal: {moon_sidereal:.6f}")
    # print(f"🌞 Sun sidereal: {sun_sidereal:.6f}")
    # print(f"📐 Tithi angle (Moon - Sun): {tithi_angle:.6f}")
    # print(f"🔢 Karana index: {karana_index}")
    # print(f"🪔 Karana resolved: {karana}")

    return karana

def compute_yoga(moon_sidereal, sun_sidereal):
    yoga_index = int((moon_sidereal + sun_sidereal) % 360 // (360 / 27))
    return YOGA_NAMES[yoga_index]

def lookup_city(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    response = requests.get(url, params=params, headers={"User-Agent": "birth-chart-app"})
    data = response.json()
    if not data:
        raise ValueError("City not found")

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    tf = TimezoneFinder()
    tz_string = tf.timezone_at(lat=lat, lng=lon)
    if tz_string is None:
        tz_string = tf.closest_timezone_at(lat=lat, lng=lon) or "Etc/GMT"

    tz = pytz.timezone(tz_string)
    utc_offset = tz.utcoffset(dt.datetime.now()).total_seconds() / 3600

    return lat, lon, utc_offset, tz_string

def compute_planets(jd_ut, lat, lon, flags=swe.FLG_SWIEPH | swe.FLG_SIDEREAL):
    positions = []
    for name, planet_code in PLANETS.items():   # name is "Sun", planet_code is swe.SUN
        planet_pos, ret = swe.calc_ut(jd_ut, planet_code, flags)
        lon = planet_pos[0]
        abs_lon = lon % 360
        sign = SIGNS[int(abs_lon // 30)]
        positions.append({
            "name": name,
            "lon": lon,
            "abs_lon": abs_lon,
            "sign": sign
        })

    # Ascendant (Lagna)
    houses = swe.houses(jd_ut, lat, lon, b'A')
    asc_lon = houses[1][0] % 360
    asc_sign = SIGNS[int(asc_lon // 30)]
    positions.append({
        "name": "Ascendant",
        "lon": asc_lon,
        "abs_lon": asc_lon,
        "sign": asc_sign
    })
    return positions

def generate_birth_chart(
    dob,
    tob,
    name=None,
    city=None,
    lat=None,
    lon=None,
    utc_offset=None,
    jd_ut=None,
    sidereal_positions=None,
    tz_string=None
    ):

    chart_dict = {}
    chart_dict["NAME"] = name

    # Convert DOB and TOB into datetime objects
    dob_obj = dt.datetime.strptime(dob, "%Y-%m-%d").date()
    tob_obj = dt.datetime.strptime(tob, "%H:%M:%S").time()
    dt_obj  = dt.datetime.combine(dob_obj, tob_obj)

    chart_dict["REFERENCE_DATETIME"] = dt_obj
    chart_dict["WEEKDAY"] = dt_obj.strftime("%A")

    chart_dict = {
        "NAME": name,
        "DOB": dob,
        "TOB": tob,
        "CITY": city,
        "LAT": lat,
        "LON": lon,
        "UTC_OFFSET": utc_offset,
        "JD_UT": jd_ut,
    }

    # Use provided positions or compute once with lat/lon to include Ascendant
    positions = sidereal_positions if sidereal_positions else get_sidereal_positions(jd_ut, lat=lat, lon=lon)
    chart_dict["PLANETS"] = positions

    # Normalize and populate LONG/ABS/SIGN for each planet using existing helpers
    for planet, pdata in positions.items():
        abs_val = ensure_float(pdata.get("ABS"), label=planet)
        dms_str, abs_lon, sign = get_sign_and_abs(abs_val)
        suffix = planet_map[planet]
        chart_dict[f"LONG_{suffix}"] = dms_str
        chart_dict[f"ABS_{suffix}"]  = f"{abs_lon:.4f}"
        chart_dict[f"SIGN_{suffix}"] = sign

    # Ascendant row if present
    if "Ascendant" in positions:
        asc = positions["Ascendant"]
        chart_dict["LONG_ASC"] = asc["LONG"]
        chart_dict["ABS_ASC"]  = f"{asc['ABS']:.4f}"
        chart_dict["SIGN_ASC"] = asc["SIGN"]

    # Parse DOB and TOB components for legacy signatures
    year, month, day = map(int, dob.split("-"))
    parts = tob.split(":")
    hour   = int(parts[0]) if len(parts) > 0 else 0
    minute = int(parts[1]) if len(parts) > 1 else 0
    second = int(parts[2]) if len(parts) > 2 else 0

    # Extract Sun and Moon sidereal longitudes from positions
    sun_sidereal  = ensure_float(positions["Sun"]["ABS"], label="Sun")
    moon_sidereal = ensure_float(positions["Moon"]["ABS"], label="Moon")

    # Legacy Panchanga computations — exact signatures from your snapshot
    chart_dict["TITHI"] = str(compute_tithi(moon_sidereal, sun_sidereal, year, month, day, hour, minute, second, float(utc_offset)))
    chart_dict["TITHI_TRANSITIONS"] = str(get_tithi_transitions(year, month, day, hour, minute, second, float(utc_offset)))
    chart_dict["NAKSHATRA"] = str(compute_nakshatra(moon_sidereal, jd_ut, float(utc_offset)))
    chart_dict["KARANA"] = str(compute_karana(moon_sidereal, sun_sidereal))
    chart_dict["YOGA"] = str(compute_yoga(moon_sidereal, sun_sidereal))
    chart_dict["WEEKDAY"] = str(compute_weekday(year, month, day))
    # --- Sunrise/Sunset using your combined helper ---
    try:
        dt_obj = datetime(year, month, day, hour, minute, second)
        sunrise, sunset = get_sunrise_sunset(city, dt_obj, jd_ut, tz_string)
        chart_dict["SUNRISE"] = str(sunrise)
        chart_dict["SUNSET"]  = str(sunset)
    except Exception as e:
        chart_dict["SUNRISE"] = f"Error: {e}"
        chart_dict["SUNSET"]  = f"Error: {e}"


    # Optional: end timings for Karana/Yoga, formatted to IST
    try:
        t0 = datetime(year, month, day, hour, minute, second)
        end_info = current_karana_yoga_end(t0, positions)

        karana_dt = end_info.get("karana_end")
        yoga_dt   = end_info.get("yoga_end")

        chart_dict["KARANA_END"] = format_end_time(karana_dt, t0, tz_string)
        chart_dict["YOGA_END"]   = format_end_time(yoga_dt, t0, tz_string)
    except Exception as e:
        chart_dict["KARANA_END"] = f"Error: {e}"
        chart_dict["YOGA_END"]   = f"Error: {e}"



    # If you wish to show a single "TITHI_END" value in preview, derive it from Tithi transitions here.
    # Assuming get_tithi_transitions returns a structure you can pick the next end from:
    try:
        transitions = get_tithi_transitions(year, month, day, hour, minute, second, float(utc_offset))
        # If transitions is a list of (end_dt_utc, tithi_number) pairs, pick the first end:
        if isinstance(transitions, (list, tuple)) and transitions:
            t0_local = datetime(year, month, day, hour, minute, second)
            chart_dict["TITHI_END"] = format_end_time(transitions[0][0], t0_local, "Asia/Kolkata")
    except Exception:
        pass  # Leave unset if your transitions format differs

    return chart_dict

def format_end_time(dt_utc, t0_utc, ist_tz):
    # Ensure both are timezone-aware
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    if t0_utc.tzinfo is None:
        t0_utc = t0_utc.replace(tzinfo=timezone.utc)

    local = dt_utc.astimezone(ist_tz)
    s = local.strftime("%d-%b-%Y %I:%M %p IST")

    if local.date() > t0_utc.astimezone(ist_tz).date():
        s += " (continues to next day)"
    return s

def current_karana_yoga_end(t0, sidereal_positions):
    """
    Compute current Karana/Yoga names and their end times.
    t0: datetime (UTC, tz-aware)
    sidereal_positions: dict with keys including "Sun" and "Moon"
        Values are sidereal longitudes in degrees.
    """

    # --- Current angles and rates ---
    Ls = sidereal_positions["Sun"]   # Sun longitude
    Lm = sidereal_positions["Moon"]  # Moon longitude

    dLs = 0.9856    # Sun mean daily motion (deg/day)
    dLm = 13.176    # Moon mean daily motion (deg/day)

    Delta = (Lm - Ls) % 360.0        # Moon - Sun
    Y     = (Lm + Ls) % 360.0        # Moon + Sun
    rate_delta = dLm - dLs
    rate_yoga  = dLm + dLs

    # --- Next boundaries ---
    karana_step = 6.0
    yoga_step   = 13.3333333333  # 13°20'
    next_karana = math.ceil(Delta / karana_step) * karana_step
    next_yoga   = math.ceil(Y / yoga_step) * yoga_step

    # --- Initial estimates ---
    d_angle_k = (next_karana - Delta) % 360.0
    d_angle_y = (next_yoga - Y) % 360.0
    dt_k_est  = d_angle_k / max(rate_delta, 1e-6)
    dt_y_est  = d_angle_y / max(rate_yoga, 1e-6)

    # --- Refinement helper ---
    def refine(lo, hi, boundary, mode="karana"):
        for _ in range(12):
            tm = lo + (hi - lo) / 2
            delta_days = (tm - t0).total_seconds() / 86400.0
            Ls_m = Ls + dLs * delta_days
            Lm_m = Lm + dLm * delta_days
            val = (Lm_m - Ls_m) % 360.0 if mode == "karana" else (Lm_m + Ls_m) % 360.0
            if val < boundary:
                lo = tm
            else:
                hi = tm
        return hi.replace(tzinfo=timezone.utc)  # attach tzinfo once here

    # --- Refine both ---
    t_k_end = refine(t0, t0 + timedelta(days=dt_k_est), next_karana, mode="karana")
    t_y_end = refine(t0, t0 + timedelta(days=dt_y_est), next_yoga, mode="yoga")

    # --- Karana name mapping ---
    karana_names_cycle = ["Bava", "Balava", "Kaulava", "Taitila",
                          "Garaja", "Vanija", "Vishti"]
    fixed_start = ["Kimstughna"]
    fixed_end   = ["Sakuni", "Chatushpada", "Nagavamsa"]

    half_tithi_index = int(Delta // 6)  # 0–59
    if half_tithi_index == 0:
        karana_name = fixed_start[0]
    elif half_tithi_index >= 57:
        karana_name = fixed_end[half_tithi_index - 57]
    else:
        karana_name = karana_names_cycle[(half_tithi_index - 1) % 7]

    # --- Yoga name mapping ---
    yoga_names = [
        "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
        "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
        "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
        "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
        "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
        "Indra", "Vaidhriti"
    ]
    yoga_index = int(Y // yoga_step) % 27
    yoga_name = yoga_names[yoga_index]

    return {
        "karana_name": karana_name,
        "karana_end": t_k_end,
        "yoga_name": yoga_name,
        "yoga_end": t_y_end,
        "karana_boundary": next_karana,
        "yoga_boundary": next_yoga
    }

def output_chart(chart_dict):
    print("\n📋 Panchanga Preview")
    print(f"NAME            {chart_dict['NAME']}")
    print(f"DATE            {chart_dict['DATE']}")
    print(f"TIME            {chart_dict['TIME']}")
    print(f"PLACE           {chart_dict['PLACE']}")
    print(f"WEEKDAY         {chart_dict['WEEKDAY']}")
    print(f"TELUGU_YEAR     {chart_dict['TELUGU_YEAR']}")
    print(f"TITHI           {chart_dict['TITHI']}")
    print(f"TITHI_END       {chart_dict['TITHI_END']}")
    print(f"NAKSHATRA       {chart_dict['NAKSHATRA']}")
    print(f"NAK_END         {chart_dict['NAK_END']}")
    print(f"KARANA          {chart_dict['KARANA']}")
    print(f"YOGA            {chart_dict['YOGA']}")

    # 🪐 Planetary Positions
    print("\n🪐 Planetary Positions")
    signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    for name, lon in chart_dict["PLANETS"].items():
        sign_index = int(lon // 30)
        sign = signs[sign_index]
        print(f"{name:10} {lon:6.2f} {sign}")

def get_sign_and_abs(lon: float):
    """
    Given a planet's longitude (0–360), return:
      - dms_str: degrees, minutes, seconds within its sign (e.g. '21°14\'32.34"')
      - abs_lon: absolute longitude float (e.g. 171.1234)
      - sign: zodiac sign abbreviation (e.g. 'Vi')
    """
    # Absolute longitude float
    abs_lon = lon

    # Degrees within the sign
    deg = int(lon % 30)
    # Minutes within the degree
    mins = int((lon * 60) % 60)
    # Seconds within the minute (fractional)
    secs = (lon * 3600) % 60

    # Format D:M:S string
    dms_str = f"{deg}°{mins:02d}'{secs:05.2f}\""

    # Zodiac sign abbreviation
    sign_index = int(lon // 30)
    sign = ZODIAC[sign_index]
    
    print("DEBUG get_sign_and_abs returned:", dms_str, abs_lon, sign, type(abs_lon))
    return dms_str, abs_lon, sign

def get_panchanga_details(jd_ut, lat, lon):
    # Sunrise and sunset
    sunrise = swe.rise_trans(jd_ut, swe.SUN, lon, lat, rsmi=swe.CALC_RISE)[1][0]
    sunset  = swe.rise_trans(jd_ut, swe.SUN, lon, lat, rsmi=swe.CALC_SET)[1][0]

    # Tithi: difference between Moon and Sun longitude / 12°
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, SE_FLAGS_DEFAULT)[0] % 360.0
    sun_lon  = swe.calc_ut(jd_ut, swe.SUN, SE_FLAGS_DEFAULT)[0] % 360.0
    tithi_num = int(((moon_lon - sun_lon) % 360.0) / 12) + 1

    # Nakshatra: Moon longitude / 13°20'
    nak_num = int(moon_lon / (360.0/27)) + 1
    pada_num = int((moon_lon % (360.0/27)) / (360.0/108)) + 1

    return {
        "Sunrise": sunrise,
        "Sunset": sunset,
        "Tithi": tithi_num,
        "Nakshatra": nak_num,
        "Pada": pada_num,
        "Weekday": swe.day_of_week(jd_ut),
    }