# --- Imports ---
import swisseph as swe
import datetime as dt
from datetime import timedelta, timezone  
from zoneinfo import ZoneInfo
import math
import requests
from timezonefinder import TimezoneFinder
import pytz

# --- Constants ---
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# Set ephemeris path
swe.set_ephe_path("C:/Users/murth/Downloads/Swisseph_extractions_13Nov25/ephe")

# Sidereal mode
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL

def get_telugu_year(gregorian_year):
    """
    Map a Gregorian year to a Telugu year name.
    For now, this is a placeholder. You can expand with the full 60-year cycle.
    """
    telugu_years = [
        "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajāpati", "Āngirasa", "Shrīmukha",
        "Bhāva", "Yuvā", "Dhātu", "Īśvara", "Bahudhānya", "Pramāthi", "Vikrama", "Vrisha",
        "Chitrabhānu", "Svabhānu", "Tārana", "Pārthiva", "Vyaya", "Sarvajit", "Sarvadhāri",
        "Virodhi", "Vikruti", "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
        "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava", "Shubhakrit", "Shobhakrith",
        "Krodhi", "Visvavasu", "Parābhava", "Plavanga", "Kīlaka", "Saumya", "Sādhāraṇa",
        "Virodhikruth", "Paridhāvi", "Pramādi", "Ānanda", "Rākshasa", "Nala", "Pingala",
        "Kālayukti", "Siddhārthi", "Raudri", "Durmati", "Dundubhi", "Rudhirodgāri", "Raktākshi",
        "Krodhana", "Akshaya"
    ]
    # Telugu cycle repeats every 60 years starting from 1987 (Prabhava)
    cycle_start = 1987
    index = (gregorian_year - cycle_start) % 60
    return telugu_years[index]
# --- Utility Functions ---
def tz_to_offset(tz_string, dob, tob):
    year, month, day = map(int, dob.split("-"))
    hour, minute, second = map(int, tob.split(":"))
    dt = datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(tz_string))
    offset = dt.utcoffset().total_seconds() / 3600.0
    return offset


def lookup_city(city_name):
    # Use OpenStreetMap Nominatim
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    response = requests.get(url, params=params, headers={"User-Agent": "birth-chart-app"})
    data = response.json()
    if not data:
        raise ValueError("City not found")

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    # Find timezone from lat/lon
    tf = TimezoneFinder()
    tz_string = tf.timezone_at(lat=lat, lng=lon)
    if tz_string is None:
        tz_string = "Asia/Kolkata"  # fallback

    tz = pytz.timezone(tz_string)
    utc_offset = tz.utcoffset(dt.datetime.now()).total_seconds() / 3600

    return lat, lon, utc_offset, tz_string


def get_sunrise_sunset(city_name, dt_obj, df, tz_string):
    """
    Compute local sunrise and sunset for given city/date/time.
    Uses existing lookup_city() and tz_to_offset() functions.
    """
    # Step 1: lookup city → lat, lon, utc_offset (from Excel df)
    lat, lon, utc_offset,tz_string = lookup_city(city_name, df)

    # Step 2: compute UTC sunrise/sunset
    # if isinstance(dob, str):
    #     dob = datetime.strptime(dob, "%Y-%m-%d").date()
    # elif isinstance(dob, datetime.datetime):
    #     dob = dob.date()
    
    # Step 3: compute UTC sunrise/sunset
    sun = Sun(lat, lon)
    sunrise_utc = sun.get_sunrise_time(dt_obj)
    sunset_utc  = sun.get_sunset_time(dt_obj)

    # Step 3: get precise offset using your tz_to_offset()
    offset = tz_to_offset(
        tz_string,
        dt_obj.strftime("%Y-%m-%d"),
        dt_obj.strftime("%H:%M:%S")
    )


    # Step 4: get precise offset using tz_to_offset()
    #offset = tz_to_offset(tz_string, dob.strftime("%Y-%m-%d"), tob.strftime("%H:%M:%S"))

    # Step 5: apply offset
    sunrise_local = sunrise_utc + timedelta(hours=offset)
    sunset_local  = sunset_utc + timedelta(hours=offset)

    return sunrise_local, sunset_local

# --- Astronomical Calculations ---
def compute_julian_day(dob, tob, utc_offset):
    year, month, day = map(int, dob.split("-"))
    hour, minute, second = map(int, tob.split(":"))

    # ✅ Force conversion here
    utc_offset = float(utc_offset)

    # Local → UTC
    ut_hour = hour - utc_offset
    ut = ut_hour + minute/60.0 + second/3600.0

    jd_ut = swe.julday(year, month, day, ut, swe.GREG_CAL)
    return jd_ut

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

def get_sidereal_positions(jd_ut, flags):
    
    positions = {}

    for name, planet in PLANETS.items():
        planet_pos, ret = swe.calc_ut(jd_ut, swe.MOON, flags)
        abs_lon = planet_pos[0] % 360   # Moon’s normalized longitude
        ayanamsa = swe.get_ayanamsa(jd_ut)
        lon = (planet_pos[0] - ayanamsa) % 360
        positions[name] = lon   # assign directly to dict
    return positions

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

# --- Panchanga Elements ---
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
            nak_end = datetime(year, month, day, hour, minute)
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

# --- Chart Utilities ---
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

    return dms_str, abs_lon, sign

def vedic_day_context(dt_obj, city, tz_string):
    # Weekday index (0=Monday, 6=Sunday)
    weekday_idx = dt_obj.weekday()

    # Vedic date is just the calendar date for now
    vedic_date = dt_obj.date()

    # Localize datetime to timezone
    tz = pytz.timezone(tz_string)
    local_dt = tz.localize(dt_obj)

    # Placeholder sunrise/sunset (can be replaced with swisseph later)
    sunrise_local = local_dt.replace(hour=6, minute=0, second=0)
    sunset_local = local_dt.replace(hour=18, minute=0, second=0)

    return vedic_date, weekday_idx, sunrise_local, sunset_local

def generate_birth_chart(name, dob, tob, city, jd_ut=None, sidereal_positions=None):
    # Convert DOB and TOB into datetime objects
    # Convert DOB and TOB into datetime objects
    if isinstance(dob, dt.date):
        dob_obj = dob
    else:
        dob_obj = dt.strptime(dob, "%Y-%m-%d").date()

    if isinstance(tob, dt.time):
        tob_obj = tob
    else:
        # Accept either "HH:MM" or "HH:MM:SS"
        try:
            tob_obj = dt.strptime(tob, "%H:%M:%S").time()
        except ValueError:
            tob_obj = dt.strptime(tob, "%H:%M").time()

    dt_obj  = dt.datetime.combine(dob_obj, tob_obj)
    t0 = dt_obj  # reference datetime
    
    if sidereal_positions is None:
        sidereal_positions = {
            "Sun": "Placeholder",
            "Moon": "Placeholder",
            "Mars": "Placeholder",
            "Mercury": "Placeholder",
            "Jupiter": "Placeholder",
            "Venus": "Placeholder",
            "Saturn": "Placeholder",
            "Rahu": "Placeholder",
            "Ketu": "Placeholder"
        }

    sun_sidereal = sidereal_positions["Sun"]



    chart_dict = {}

    # Lookup city
    lat, lon, utc_offset, tz_string = lookup_city(city)

    # ✅ Vedic day context (handles pre-sunrise TOBs)
    vedic_date, weekday_idx, sunrise_local, sunset_local = vedic_day_context(dt_obj, city, tz_string)
    # Telugu year
    telugu_year = get_telugu_year(dob_obj.year)

    # Panchanga calculations
    sun_sidereal  = sidereal_positions["Sun"]
    moon_sidereal = sidereal_positions["Moon"]

    tithi_name, tithi_end, _, _ = compute_tithi(
        moon_sidereal, sun_sidereal,
        dob_obj.year, dob_obj.month, dob_obj.day,
        tob_obj.hour, tob_obj.minute, tob_obj.second,
        utc_offset
    )

    nak_name, nak_pada, nak_end = compute_nakshatra(moon_sidereal, jd_ut, utc_offset)
    nak_full = f"{nak_name} (Pada {nak_pada})"

    # Karana & Yoga
    karana = compute_karana(moon_sidereal, sun_sidereal)
    yoga_name = compute_yoga(moon_sidereal, sun_sidereal)
    kar_yog = current_karana_yoga_end(t0, sidereal_positions)

    karana_end_local = kar_yog["karana_end"].astimezone(ist_tz)
    chart_dict["KARANA_END"] = karana_end_local.strftime("%d-%b-%Y %I:%M %p IST")

    yoga_end_local = kar_yog["yoga_end"].astimezone(ist_tz)
    yoga_end_str = yoga_end_local.strftime("%d-%b-%Y %I:%M %p IST")
    if yoga_end_local.date() > t0.date():
        yoga_end_str += " (continues to next day)"

    chart_dict["KARANA"] = kar_yog["karana_name"]
    chart_dict["YOGA"]   = kar_yog["yoga_name"]
    chart_dict["YOGA_END"] = yoga_end_str

    # ✅ Tradition-honoring Rahukaalam
    rahu_start, rahu_end = compute_rahukaalam(sunrise_local, sunset_local, weekday_idx)
    rahu_str = f"{rahu_start.strftime('%I:%M %p')} - {rahu_end.strftime('%I:%M %p')}"

    # ✅ Durmuhurtam (use same sunrise anchor)
    # durmuhurtam_str = compute_durmuhurtam(sunrise_local, weekday_idx)
    chart_dict["SUN_SIDEREAL"] = sidereal_positions.get("Sun")
    # Build chart_dict
    chart_dict.update({
        "NAME": name,
        "DATE": dob,
        "TIME": tob,
        "PLACE": city,
        "WEEKDAY": vedic_date.strftime("%A"),  # Vedic weekday
        "LAT": lat,
        "LONG": lon,
        "TELUGU_YEAR": telugu_year,
        "TITHI": tithi_name,
        "TITHI_END": tithi_end,
        "NAKSHATRA": nak_full,
        "NAK_END": nak_end,
        "PLANETS": sidereal_positions,
        "SUNRISE": sunrise_local.strftime("%I:%M %p"),
        "SUNSET": sunset_local.strftime("%I:%M %p")
    })



    # ✅ Ask user choice
    choice = input("\nDo you want to populate PPTX? (y/n): ").strip().lower()
    if choice == "y":
        fill_pptx(chart_dict, template_file="Template_BChart_A4.pptx")
    else:
        print("❌ Skipping PPTX population. Output shown on screen only.")

    return chart_dict
 