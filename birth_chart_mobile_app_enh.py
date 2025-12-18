import os
import datetime as dt
import pytz
import swisseph as swe

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
import traceback
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import requests
from timezonefinder import TimezoneFinder
from datetime import datetime
import math
from math import *
from datetime import timedelta
from zoneinfo import ZoneInfo
from datetime import timezone


SIGNS = {
    0:"Ar", 1:"Ta", 2:"Ge", 3:"Cn",
    4:"Le", 5:"Vi", 6:"Li", 7:"Sc",
    8:"Sg", 9:"Cp", 10:"Aq", 11:"Pi"
}
planet_abbr = {
    "Sun":"Su","Moon":"Mo","Mars":"Ma","Mercury":"Me",
    "Jupiter":"Ju","Venus":"Ve","Saturn":"Sa",
    "Rahu":"Ra","Ketu":"Ke","Ascendant":"Asc"
}

TELUGU_YEAR_NAMES = [
    "Prabhava", "Vibhava", "Sukla", "Pramodoota", "Prajotpatti", "Angeerasa", "Sreemukha", "Bhava", "Yuva", 
    "Dhata", "Isvara", "Bahudhaanya", "Pramadhi", "Vikrama", "Vr̥uṣha", "Chitrabhanu", "Svabhaanu", "Taaraṇa", 
    "Paarthiva", "Vyaya", "Sarvajittu", "Sarvadhari", "Virodhi", "Vikr̥uti", "Khara", "Nandana", "Vijaya", "Jaya",
    "Manmadha", "Durmukhi", "Hevaḷambi", "Viḷambi", "Vikaari", "Saarvari", "Plava", "Subhakr̥ut", "Sobhakr̥ut",
    "Krodhi", "Viswaavasu", "Paraabhava", "Plavanga", "Keelaka", "Saumya", "Saadharaṇa", "Virodhikr̥ut", "Pareedhavi",
    "Pramaadeecha", "Ananda", "Raakṣhasa", "Nala", "Pingaḷa", "Kaaḷayukti", "Siddharthi", "Raudri", "Durmati", "Dundubhi",
    "Rudhirodgari", "Raktaakṣhi", "Krodhana", "Akṣaya"
]

SIGN_RANGES = {
    "Ar": (0.0, 29.9999),    # Aries
    "Ta": (30.0, 59.9999),   # Taurus
    "Ge": (60.0, 89.9999),   # Gemini
    "Cn": (90.0, 119.9999),  # Cancer
    "Le": (120.0, 149.9999), # Leo
    "Vi": (150.0, 179.9999), # Virgo
    "Li": (180.0, 209.9999), # Libra
    "Sc": (210.0, 239.9999), # Scorpio
    "Sg": (240.0, 269.9999), # Sagittarius
    "Cp": (270.0, 299.9999), # Capricorn
    "Aq": (300.0, 329.9999), # Aquarius
    "Pi": (330.0, 359.9999)  # Pisces
}

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

ZODIAC = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]

KARANA_SEQUENCE = (
    ["Kimstughna"]
    + ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"] * 8
    + ["Shakuni", "Chatushpada", "Naga"]
)
flags = swe.FLG_SWIEPH | swe.FLG_SPEED
planet_map = {
                "Sun": "Su", "Moon": "Mo", "Mercury": "Me", "Venus": "Ve",
                "Mars": "Ma", "Jupiter": "Ju", "Saturn": "Sa",
                "Rahu": "Ra", "Ketu": "Ke", "Ascendant": "Asc"
}

WEEKDAY_NAMES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

class StyledDropDown(DropDown):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Reduce spacing/padding between items
        self.container.spacing = 0
        self.container.padding = [0, 0, 0, 0]

    def add_widget(self, widget, index=0):
        # Apply styling to dropdown items
        if isinstance(widget, Button):
            widget.font_size = 18        # larger font for readability
            widget.height = 32           # tighter row height
            widget.background_normal = ""
            widget.background_color = (0.95, 0.95, 1, 1)
            widget.color = (0, 0, 0, 1)
        return super().add_widget(widget, index)

class AutoCompleteTextInput(TextInput):
    def __init__(self, values, **kwargs):
        super().__init__(**kwargs)
        self.values = values
        self.dropdown = DropDown()
        self.bind(text=self.on_text)

    def on_text(self, instance, value):
        # Clear old suggestions
        self.dropdown.clear_widgets()

        if not value:
            # If text is empty, close dropdown
            self.dropdown.dismiss()
            return

        # Add matching suggestions
        for v in self.values:
            if v.startswith(value):
                btn = Button(
                    text=v,
                    size_hint_y=None,
                    height=32,
                    background_normal="",
                    background_color=(0.95, 0.95, 1, 1),
                    color=(0, 0, 0, 1),
                    font_size=18
                )
                btn.bind(on_release=lambda btn: self.select_value(btn.text))
                self.dropdown.add_widget(btn)

        # Only open if there are suggestions, widget is focused, and dropdown not already open
        if self.dropdown.children and self.focus:
            self.dropdown.dismiss()   # ensure closed before reopening
            self.dropdown.open(self)

    def select_value(self, val):
        self.text = val
        self.dropdown.dismiss()

class PanchangaApp(App):
    def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.chart_data = None

    def validate_dob_inputs(self):
        inputs = {
            "Day": self.day_spinner,
            "Month": self.month_spinner,
            "Year": self.year_input,   # corrected reference
            "Hour": self.hour_spinner,
            "Minute": self.minute_spinner,
            "Second": self.second_spinner
        }

        for label, spinner in inputs.items():
            val = spinner.text.strip()
            if val == label or val == "" or not val.isdigit():
                raise ValueError(f"Please select a valid {label}.")
        
    def build(self):
        Window.size = (414, 896)

        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        root.canvas.before.clear()
        with root.canvas.before:
            Color(1, 1, 1, 1)  # pure white background
            self.bg_rect = Rectangle(size=Window.size, pos=root.pos)

        input_height = 34
        input_width = 0.25

        input_grid = GridLayout(cols=2, spacing=5, size_hint_y=None)
        input_grid.bind(minimum_height=input_grid.setter('height'))

        def add_input(label_text, widget):
            input_grid.add_widget(Label(
                text=label_text,
                size_hint=(input_width, None),
                height=input_height,
                color=(1, 1, 1, 1)   # black text
            ))
            input_grid.add_widget(widget)

        # Inputs
        self.name_input = TextInput(
            hint_text="Name", size_hint=(input_width, None), height=input_height,
            background_normal="", background_color=(0.95, 0.95, 1, 1),
            foreground_color=(0, 0, 0, 1)
        )
        add_input("Name:", self.name_input)

        # Day spinner
        self.day_spinner = Spinner(
            text="Day",
            values=[str(i) for i in range(1, 32)],
            size_hint=(input_width, None),
            height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1),
            color=(0,0,0,1),
            dropdown_cls=StyledDropDown
        )
        add_input("Day:", self.day_spinner)

        # Month spinner
        self.month_spinner = Spinner(
            text="Month",
            values=[str(i) for i in range(1, 13)],
            size_hint=(input_width, None),
            height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1),
            color=(0,0,0,1),
            dropdown_cls=StyledDropDown
        )
        add_input("Month:", self.month_spinner)

        # Year input
        self.year_input = AutoCompleteTextInput(
            values=[str(y) for y in range(1900, 2101)],
            hint_text="Year",
            size_hint=(input_width, None),
            height=input_height,
            background_normal="", background_color=(0.95, 0.95, 1, 1),
            foreground_color=(0, 0, 0, 1)
        )
        self.year_input.text = str(dt.datetime.now().year)
        add_input("Year:", self.year_input)

        self.city_input = TextInput(
            hint_text="City", size_hint=(input_width, None), height=input_height,
            background_normal="", background_color=(0.95, 0.95, 1, 1),
            foreground_color=(0, 0, 0, 1)
        )
        add_input("City:", self.city_input)

        # Time row
        time_box = BoxLayout(orientation='horizontal', spacing=5,
                            size_hint_y=None, height=input_height)

        self.hour_spinner = Spinner(
            text="Hour",
            values=[f"{i:02d}" for i in range(0,24)],
            size_hint=(0.1, None),
            height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1),
            color=(0,0,0,1),
            dropdown_cls=StyledDropDown
        )

        self.minute_spinner = Spinner(
            text="Minute",
            values=[f"{i:02d}" for i in range(0,60)],
            size_hint=(0.1, None),
            height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1),
            color=(0,0,0,1),
            dropdown_cls=StyledDropDown
        )

        self.second_spinner = Spinner(
            text="Second",
            values=[f"{i:02d}" for i in range(0,60)],
            size_hint=(0.1, None),
            height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1),
            color=(0,0,0,1),
            dropdown_cls=StyledDropDown
        )

        now = dt.datetime.now()
        self.day_spinner.text = str(now.day)
        self.month_spinner.text = str(now.month)
        self.year_input.text = str(now.year)
        self.hour_spinner.text = f"{now.hour:02d}"
        self.minute_spinner.text = f"{now.minute:02d}"
        self.second_spinner.text = f"{now.second:02d}"

        time_box.add_widget(Label(text="Time:", size_hint=(0.15, None),
                                height=input_height, color=(1,1,1,1)))
        time_box.add_widget(self.hour_spinner)
        time_box.add_widget(self.minute_spinner)
        time_box.add_widget(self.second_spinner)

        root.add_widget(input_grid)
        root.add_widget(time_box)

        # Buttons row
        button_font_size = 16
        button_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=45, spacing=8, padding=(20, 0))

        generate_btn = Button(
            text="Generate", size_hint_x=0.22, font_size=button_font_size,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )
        save_pdf_btn = Button(
            text="Save PDF", size_hint_x=0.22, font_size=button_font_size,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )
        reset_btn = Button(
            text="Reset", size_hint_x=0.22, font_size=button_font_size,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )
        exit_btn = Button(
            text="Exit", size_hint_x=0.22, font_size=button_font_size,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )

        # Wire buttons
        generate_btn.bind(on_press=self.on_generate)
        save_pdf_btn.bind(on_press=self.on_save_pdf)
        reset_btn.bind(on_press=self.on_reset)   # <-- wired Reset button
        exit_btn.bind(on_press=lambda *args: App.get_running_app().stop())

        button_box.add_widget(generate_btn)
        button_box.add_widget(save_pdf_btn)
        button_box.add_widget(reset_btn)
        button_box.add_widget(exit_btn)

        root.add_widget(button_box)

        # Scrollable output area
        scroll = ScrollView(size_hint=(1, 1))
        self.output_label = Label(
            text="",
            font_size=16,
            halign="left",
            valign="top",
            size_hint_y=None,
            text_size=(Window.width - 20, None),
            padding=(10, 10),
            size_hint_x=None,
            width=Window.width - 20,
            color=(0, 0, 0, 1)
        )
        self.output_label.bind(
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        return root
    
    def on_save_pdf(self, *_):
        """Save the generated chart output into a PDF file with improved formatting."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            import pytz, datetime as dt, swisseph as swe

            # Helper: safely get text from spinner or text input
            def get_text(attr_candidates, label):
                for attr in attr_candidates:
                    if hasattr(self, attr):
                        return getattr(self, attr).text.strip()
                raise AttributeError(f"Missing {label} input (expected one of {attr_candidates})")

            # Collect inputs
            name  = get_text(['name_input'], 'NAME')
            city  = get_text(['city_input'], 'PLACE')
            year   = int(get_text(['year_input','year_spinner'], 'YEAR'))
            month  = int(get_text(['month_input','month_spinner'], 'MONTH'))
            day    = int(get_text(['day_input','day_spinner'], 'DAY'))
            hour   = int(get_text(['hour_input','hour_spinner'], 'HOUR'))
            minute = int(get_text(['minute_input','minute_spinner'], 'MINUTE'))
            second = int(get_text(['second_input','second_spinner'], 'SECOND'))

            dob = f"{year:04d}-{month:02d}-{day:02d}"
            tob = f"{hour:02d}:{minute:02d}:{second:02d}"

            # Lookup city and timezone
            lat, lon, utc_offset, tz_string = self.lookup_city(city)
            self.tz = pytz.timezone(tz_string)

            # Datetime objects
            dob_obj = dt.datetime.strptime(dob, "%Y-%m-%d").date()
            tob_obj = dt.datetime.strptime(tob, "%H:%M:%S").time()
            dt_obj = dt.datetime.combine(dob_obj, tob_obj)

            # Swiss Ephemeris setup
            jd_local = swe.julday(
                dt_obj.year, dt_obj.month, dt_obj.day,
                dt_obj.hour + dt_obj.minute / 60 + dt_obj.second / 3600,
                swe.GREG_CAL
            )
            jd_ut = jd_local - (utc_offset / 24.0)
            swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

            def calc_lon(body):
                return swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]

            # Planetary positions
            rahu = calc_lon(swe.MEAN_NODE) % 360
            sidereal_positions = {
                "Sun":      calc_lon(swe.SUN)     % 360,
                "Moon":     calc_lon(swe.MOON)    % 360,
                "Mars":     calc_lon(swe.MARS)    % 360,
                "Mercury":  calc_lon(swe.MERCURY) % 360,
                "Jupiter":  calc_lon(swe.JUPITER) % 360,
                "Venus":    calc_lon(swe.VENUS)   % 360,
                "Saturn":   calc_lon(swe.SATURN)  % 360,
                "Rahu":     rahu,
                "Ketu":     (rahu + 180) % 360,
            }

            # Houses and Ascendant
            houses, ascmc = swe.houses(jd_ut, lat, lon, b'P')
            asc_tropical = ascmc[0]
            ayan = swe.get_ayanamsa(jd_ut)
            asc_sidereal = (asc_tropical - ayan) % 360
            sidereal_positions["Ascendant"] = asc_sidereal

            chart = self.generate_birth_chart(
                name, dob, tob, city, lat, lon, utc_offset,
                jd_ut, sidereal_positions
            )

            # Telugu year cleanup
            telugu_year = chart.get("TELUGU_YEAR", "").replace("(", "").replace(")", "").replace("☒", "").strip()

            # PDF file
            filename = f"{name}_birth_chart.pdf"
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Top title
            title = f"Birth Chart for {name}".upper()
            c.setFont("Helvetica-Bold", 16)  # larger title font
            c.drawCentredString(width / 2, height - 50, title)

            # Section 1: Birth Data – Panchangam Details
            y = height - 90
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "BIRTH DATA – PANCHANGAM DETAILS")
            y -= 25

            c.setFont("Courier", 11)  # larger font for details
            info_fields = [
                ("NAME", name),
                ("DATE", dob),
                ("TIME", tob),
                ("PLACE", city),
                ("WEEKDAY", dt_obj.strftime('%A')),
                ("LAT", f"{lat}"),
                ("LONG", f"{lon}"),
                ("TELUGU_YEAR", telugu_year),
                ("TITHI", chart.get("TITHI", "")),
                ("TITHI_END", chart.get("TITHI_END", "")),
                ("NAKSHATRA", chart.get("NAKSHATRA", "")),
                ("NAK_END", chart.get("NAK_END", "")),
                ("KARANA", chart.get("KARANA", "")),
                ("KARANA_END", chart.get("KARANA_END", "")),
                ("YOGA", chart.get("YOGA", "")),
                ("YOGA_END", chart.get("YOGA_END", "")),
            ]
            for lbl, val in info_fields:
                c.drawString(50, y, f"{lbl:<13} : {val}")
                y -= 18  # slightly more spacing

            # Section 2: Rāśi Chakra Diagram
            chart_x = 330
            chart_y = height - 310
            self.draw_south_indian_chart(c, chart_x, chart_y, 220, sidereal_positions, dob, tob)  # slightly larger chart

            # Section 3: Planet Positions
            y -= 40
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "PLANET POSITIONS")
            y -= 30

            data = [["Planet", "Longitude", "ABS.Longitude", "Sign"]]
            for planet in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu", "Ascendant"]:
                prefix = planet[:2] if planet != "Ascendant" else "Asc"
                data.append([
                    planet,
                    chart.get(f"LONG_{prefix}", ""),
                    chart.get(f"ABS_{prefix}", ""),
                    chart.get(f"SIGN_{prefix}", ""),
                ])

            table = Table(data, colWidths=[100, 120, 120, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),   # header row only
                ('FONTNAME', (0,1), (-1,-1), 'Courier'),      # body rows only
                ('FONTSIZE', (0,0), (-1,-1), 12),
                ('LEFTPADDING',(0,0),(-1,-1),6),
                ('RIGHTPADDING',(0,0),(-1,-1),6),
            ]))

            table3_width, table3_height = table.wrap(0, 0)
            x_center = (width - table3_width) / 2
            table.drawOn(c, x_center, y - table3_height)

            c.save()
            self.output_label.text += f"\n\nPDF saved as {filename}"

        except Exception as e:
            self.output_label.text += f"\n\nError saving PDF: {e}"
   
    def on_reset(self, *args):
        now = dt.datetime.now()

        # Reset spinners
        self.day_spinner.text = str(now.day)
        self.month_spinner.text = str(now.month)
        self.hour_spinner.text = f"{now.hour:02d}"
        self.minute_spinner.text = f"{now.minute:02d}"
        self.second_spinner.text = f"{now.second:02d}"

        # Reset year input (AutoCompleteTextInput)
        self.year_input.text = str(now.year)

        # Dismiss dropdown if still open
        if hasattr(self.year_input, 'dropdown'):
            self.year_input.dropdown.dismiss()

        # Clear name/city fields if needed
        self.name_input.text = ""
        self.city_input.text = ""

        # Clear output label
        self.output_label.text = ""
    
    def _update_rect(self, instance, value):
        """Keep background rectangle aligned with window size."""
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def get_dob_values(self):
        # Defensive parsing of year
        year_text = (self.year_input.text or "").strip()
        if not year_text.isdigit():
            raise ValueError("Please enter a valid numeric year.")

        return {
            "day": int(self.day_spinner.text.strip()),
            "month": int(self.month_spinner.text.strip()),
            "year": int(year_text),
            "hour": int(self.hour_spinner.text.strip()),
            "minute": int(self.minute_spinner.text.strip()),
            "second": int(self.second_spinner.text.strip())
        }

    def on_generate(self, *_):
        try:
            # Validate DOB inputs first
            self.validate_dob_inputs()

            dob_vals = self.get_dob_values()
            dob = f"{dob_vals['year']:04d}-{dob_vals['month']:02d}-{dob_vals['day']:02d}"
            tob = f"{dob_vals['hour']:02d}:{dob_vals['minute']:02d}:{dob_vals['second']:02d}"

            # Collect inputs
            name = self.name_input.text.strip()
            city = self.city_input.text.strip()

            # Lookup city
            lat, lon, utc_offset, tz_string = self.lookup_city(city)
            tz = pytz.timezone(tz_string)
            self.tz = tz

            # Datetime objects
            dob_obj = dt.datetime.strptime(dob, "%Y-%m-%d").date()
            tob_obj = dt.datetime.strptime(tob, "%H:%M:%S").time()
            dt_obj = dt.datetime.combine(dob_obj, tob_obj)

            jd_local = swe.julday(
                dt_obj.year, dt_obj.month, dt_obj.day,
                dt_obj.hour + dt_obj.minute/60 + dt_obj.second/3600,
                swe.GREG_CAL
            )
            jd_ut = jd_local - (utc_offset / 24.0)
            swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

            def calc_lon(body):
                return swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]

            # Planetary longitudes
            sun_lon = calc_lon(swe.SUN)
            moon_lon = calc_lon(swe.MOON)
            mars_lon = calc_lon(swe.MARS)
            mercury_lon = calc_lon(swe.MERCURY)
            jupiter_lon = calc_lon(swe.JUPITER)
            venus_lon = calc_lon(swe.VENUS)
            saturn_lon = calc_lon(swe.SATURN)
            rahu_lon = calc_lon(swe.MEAN_NODE)
            ketu_lon = (rahu_lon + 180) % 360

            houses, ascmc = swe.houses(jd_ut, lat, lon, b'P')
            asc_tropical = ascmc[0]
            ayan = swe.get_ayanamsa(jd_ut)
            asc_sidereal = (asc_tropical - ayan) % 360

            sidereal_positions = {
                "Sun": sun_lon % 360,
                "Moon": moon_lon % 360,
                "Mars": mars_lon % 360,
                "Mercury": mercury_lon % 360,
                "Jupiter": jupiter_lon % 360,
                "Venus": venus_lon % 360,
                "Saturn": saturn_lon % 360,
                "Rahu": rahu_lon % 360,
                "Ketu": ketu_lon % 360,
                "Ascendant": asc_sidereal
            }

            # Generate chart silently (no PPTX prompt)
            chart = self.generate_birth_chart(
                name, dob, tob, city, lat, lon, utc_offset,
                jd_ut, sidereal_positions
            )

            # Font fallback (monospaced for alignment)
            mono_path_candidates = [
                r"C:\Windows\Fonts\consola.ttf",
                r"C:\Windows\Fonts\cour.ttf",
                r"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                r"/System/Library/Fonts/Monaco.ttf"
            ]
            mono_font = next((p for p in mono_path_candidates if os.path.exists(p)), None)
            if mono_font:
                self.output_label.font_name = mono_font

            line_sep_40 = "=" * 40
            line_sep_56 = "=" * 56

            def fmt_info(label, value):
                return f"{label:<16} : {value}"

            info_fields = [
                ("NAME", name),
                ("DATE", dob),
                ("TIME", tob),
                ("PLACE", city),
                ("WEEKDAY", dt_obj.strftime('%A')),
                ("LAT", f"{lat}"),
                ("LONG", f"{lon}"),
                ("TELUGU_YEAR", chart.get("TELUGU_YEAR", "")),
                ("TITHI", chart.get("TITHI", "")),
                ("TITHI_END", chart.get("TITHI_END", "")),
                ("NAKSHATRA", chart.get("NAKSHATRA", "")),
                ("NAK_END", chart.get("NAK_END", "")),
                ("KARANA", chart.get("KARANA", "")),
                ("KARANA_END", chart.get("KARANA_END", "")),
                ("YOGA", chart.get("YOGA", "")),
                ("YOGA_END", chart.get("YOGA_END", ""))
            ]

            planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu", "Ascendant"]

            def fmt_planet_line(planet):
                prefix = planet[:2] if planet != "Ascendant" else "Asc"
                long_val = chart.get(f"LONG_{prefix}", "")
                abs_val  = chart.get(f"ABS_{prefix}", "")
                sign_val = chart.get(f"SIGN_{prefix}", "")
                return f"{planet:<12}{long_val:<20}{abs_val:<15}{sign_val:<5}"

            output_lines = []
            output_lines.append("📋 Panchanga Preview")
            output_lines.append(line_sep_40)
            output_lines.extend(fmt_info(lbl, val) for lbl, val in info_fields)
            output_lines.append(line_sep_40)
            output_lines.append("")
            output_lines.append("PLANET POSITIONS")
            output_lines.append(line_sep_56)
            output_lines.append(f"{'Planet':<12}{'Longitude':<20}{'ABS.Longitude':<15}{'Sign':<5}")
            output_lines.append(line_sep_56)
            output_lines.extend(fmt_planet_line(p) for p in planets)
            output_lines.append(line_sep_56)

            # Display in widget (black text on uniform background)
            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text = "\n".join(output_lines)

            # Save chart data for PPTX generation
            self.chart_data = chart

        except Exception as e:
            import traceback
            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text += f"\n\nError generating chart: {e}\n{traceback.format_exc()}"
    
    def on_exit(self, *_):
        """Gracefully stop the app when Exit button is pressed."""
        from kivy.app import App
        App.get_running_app().stop()

    def _update_text_height(self, instance, value):
        instance.height = instance.texture_size[1]
        instance.text_size = (self.output_scroll.width - 20, None)

    def get_sunrise_sunset(self,city_name, dt_obj):
        """
        Compute local sunrise and sunset times for a given city and datetime.
        Uses lookup_city() and tz_to_offset() helpers.
        """

        # Step 1: Lookup city details
        lat, lon, utc_offset, tz_string = self.lookup_city(city_name)

        # Step 2: Convert datetime to Julian Day
        jd_ut = swe.julday(
            dt_obj.year,
            dt_obj.month,
            dt_obj.day,
            dt_obj.hour + dt_obj.minute / 60.0 + dt_obj.second / 3600.0,
            swe.GREG_CAL
        )

        # Step 3: Compute UTC sunrise and sunset
        sunrise_result = swe.rise_trans(jd_ut, swe.SUN, lon, lat, rsmi=swe.CALC_RISE)
        sunset_result  = swe.rise_trans(jd_ut, swe.SUN, lon, lat, rsmi=swe.CALC_SET)

        sunrise_utc = sunrise_result[1][0]
        sunset_utc  = sunset_result[1][0]

        # Step 4: Apply timezone offset
        offset = tz_to_offset(
            tz_string,
            dt_obj.strftime("%Y-%m-%d"),
            dt_obj.strftime("%H:%M:%S")
        )

        sunrise_local = sunrise_utc + timedelta(hours=offset)
        sunset_local  = sunset_utc + timedelta(hours=offset)

        return sunrise_local, sunset_local

    def draw_south_indian_chart(self, c, x, y, size, sidereal_positions, dob, tob):
        """Draw South Indian 4x4 Rāśi Chakra with merged cells and spaced planets."""
        cell = size / 4

        # Draw horizontal lines
        for i in range(5):
            c.line(x, y + i*cell, x + size, y + i*cell)

        # Draw vertical lines, skipping merged middle block
        for j in range(5):
            if j == 2:
                # draw only top and bottom segments, leave the middle open
                c.line(x + j*cell, y + 3*cell, x + j*cell, y + size)   # top two cells
                c.line(x + j*cell, y, x + j*cell, y + cell)            # bottom cell
            else:
                c.line(x + j*cell, y, x + j*cell, y + size)

        # Fixed rāśi positions
        rasi_order = {
            "Pi": (0,0), "Ar": (0,1), "Ta": (0,2), "Ge": (0,3),
            "Aq": (1,0), "Cn": (1,3),
            "Cp": (2,0), "Le": (2,3),
            "Sg": (3,0), "Sc": (3,1), "Li": (3,2), "Vi": (3,3)
        }
        rasi_names = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]

        # Prepare planet stacking per rāśi
        rasi_planets = {rasi: [] for rasi in rasi_order}
        for planet, lon in sidereal_positions.items():
            if planet == "Ascendant":
                continue  # skip Ascendant here, handle separately
            rasi_index = int(lon // 30)
            rasi = rasi_names[rasi_index]
            if rasi in rasi_planets:
                abbr = planet_abbr.get(planet, planet[:2])
                rasi_planets[rasi].append(abbr)

        # Draw rāśi labels (smaller, gray font)
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)  # gray color
        for rasi, (row,col) in rasi_order.items():
            rx = x + col*cell
            ry = y + (3-row)*cell
            c.drawString(rx+2, ry+cell-12, rasi)
        c.setFillColorRGB(0, 0, 0)        # reset to black for planets and other text


        # Draw stacked planets with dynamic font sizing
        for rasi, planets in rasi_planets.items():
            if rasi in rasi_order and planets:
                row, col = rasi_order[rasi]
                rx = x + col*cell
                ry = y + (3-row)*cell

                count = len(planets)
                if count >= 6:
                    font_size, line_gap = 9, 10
                elif count >= 4:
                    font_size, line_gap = 10, 11
                else:
                    font_size, line_gap = 11, 12

                c.setFont("Courier", font_size)
                # center the stack vertically
                offset = (count-1) * line_gap / 2
                for i, planet in enumerate(planets):
                    c.drawCentredString(rx + cell/2, ry + cell/2 - offset + i*line_gap, planet)

        # Draw Ascendant separately as cusp marker
        asc_lon = sidereal_positions.get("Ascendant", 0)
        asc_rasi = rasi_names[int(asc_lon // 30)]
        if asc_rasi in rasi_order:
            row, col = rasi_order[asc_rasi]
            rx = x + col*cell
            ry = y + (3-row)*cell
            count = len(rasi_planets[asc_rasi])

            # dynamic font sizing based on crowd
            if count >= 6:
                font_size, line_gap = 9, 10
            elif count >= 4:
                font_size, line_gap = 10, 11
            else:
                font_size, line_gap = 11, 12

            c.setFont("Courier", font_size)

            if count == 0:
                asc_y = ry + cell/2
            else:
                offset = (count-1) * line_gap / 2
                asc_y = ry + cell/2 - offset - line_gap  # one line above the stack

            c.drawCentredString(rx + cell/2, asc_y, "Asc")

        # Merged cell: RASI CHAKRA
        rx = x + cell
        ry = y + 2*cell
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(rx + cell, ry + cell/2, "RASI CHAKRA")

        # Merged cell: DOB / TOB
        rx = x + cell
        ry = y + cell
        c.setFont("Courier-Bold", 11)
        c.drawCentredString(rx + cell, ry + cell/2 + 6, f"DOB: {dob}")
        c.drawCentredString(rx + cell, ry + cell/2 - 6, f"TOB: {tob}")

    def generate_birth_chart(self, name, dob, tob, city, lat, lon, utc_offset,jd_ut, sidereal_positions):
        # Convert DOB and TOB into datetime objects
        dob_obj = datetime.strptime(dob, "%Y-%m-%d").date()
        tob_obj = datetime.strptime(tob, "%H:%M:%S").time()
        dt_obj  = datetime.combine(dob_obj, tob_obj)
        t0 = datetime.combine(dob_obj, tob_obj)   # this is your reference datetime
        # Weekday
        weekday = dt_obj.strftime("%A")
        chart_dict = {}

        # Telugu year (placeholder – replace with your actual logic)
        telugu_year = self.get_telugu_year(dob_obj.year)

        # Panchanga calculations using sidereal values
        sun_sidereal  = sidereal_positions["Sun"]
        moon_sidereal = sidereal_positions["Moon"]

        # Tithi
        tithi_name, tithi_end, _, _ = self.compute_tithi(
            moon_sidereal, sun_sidereal,
            dob_obj.year, dob_obj.month, dob_obj.day,
            tob_obj.hour, tob_obj.minute, tob_obj.second,
            utc_offset
        )
        

        nak_name, nak_pada, nak_end = self.compute_nakshatra(moon_sidereal, jd_ut, utc_offset)
        # print("DEBUG Nakshatra raw result:", (nak_name, nak_pada, nak_end))
        nak_full = f"{nak_name} (Pada {nak_pada})"


        #print("sidereal_positions keys :", sidereal_positions.keys())
        # Karana
        karana = self.compute_karana(moon_sidereal, sun_sidereal)
        # print(f"DEBUG Karana: {karana}")
        # Yoga
        yoga_name = self.compute_yoga(moon_sidereal, sun_sidereal)
        # print(f"DEBUG Yoga: {yoga_name}")
        kar_yog = self.current_karana_yoga_end(t0, sidereal_positions)
        #print("DEBUG kar_yog dict:", kar_yog)

        # Convert to IST and format
        self.karana_end_local = kar_yog["karana_end"].astimezone(self.tz)
        self.karana_end_str = self.karana_end_local.strftime("%d-%b-%Y %I:%M %p IST")

        self.yoga_end_local = kar_yog["yoga_end"].astimezone(self.tz)
        self.yoga_end_str = self.yoga_end_local.strftime("%d-%b-%Y %I:%M %p IST")
        if self.yoga_end_local.date() > t0.date():
            self.yoga_end_str += " (continues to next day)"

        chart_dict.update({
            "NAME": name,
            "DATE": dob,
            "TIME": tob,
            "PLACE": city,
            "WEEKDAY": weekday,
            "LAT": lat,
            "LONG": lon,
            "TELUGU_YEAR": telugu_year,
            "TITHI": tithi_name,
            "TITHI_END": tithi_end,
            "NAKSHATRA": nak_full,
            "NAK_END": nak_end,
            "KARANA": karana,
            "KARANA_END": self.karana_end_str,
            "YOGA": yoga_name,
            "YOGA_END": self.yoga_end_str,
            "PLANETS": sidereal_positions
        })


        # 🔎 Final debug preview
        print("\n📋 Panchanga Preview")
        print("====================================")
        for key, val in chart_dict.items():
            if key in ("chart_data", "PLANETS"):   # skip both
                continue
            print(f"{key:12s}: {val}")
        print("====================================")
        
        for planet, lon in chart_dict["PLANETS"].items():
            dms_str, abs_lon, sign = self.get_sign_and_abs(lon)
            suffix = planet_map[planet]   # e.g. "Su", "Mo", "Asc"

            chart_dict[f"LONG_{suffix}"] = dms_str          # Column 2 → D:M:S string
            chart_dict[f"ABS_{suffix}"]  = f"{abs_lon:.4f}" # Column 3 → raw float longitude
            chart_dict[f"SIGN_{suffix}"] = sign             # Column 4 → zodiac sign abbreviation
        print("\nPLANET POSITIONS")
        print("========================================================")
        for planet, suffix in planet_map.items():
            print(f"{planet:10s} | LONG={chart_dict.get(f'LONG_{suffix}', '')} "
                f"| ABS={chart_dict.get(f'ABS_{suffix}', '')} "
                f"| SIGN={chart_dict.get(f'SIGN_{suffix}', '')}")
        print("=========================================================")

        return chart_dict
 
    def get_sidereal_positions(self, jd_ut, flags):
        
        positions = {}

        for name, planet in PLANETS.items():
            planet_pos, ret = swe.calc_ut(jd_ut, swe.MOON, flags)
            abs_lon = planet_pos[0] % 360   # Moon’s normalized longitude
            ayanamsa = swe.get_ayanamsa(jd_ut)
            lon = (planet_pos[0] - ayanamsa) % 360
            positions[name] = lon   # assign directly to dict
        return positions

    def lookup_city(self, city_name):
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

        self.tz = pytz.timezone(tz_string)
        utc_offset = self.tz.utcoffset(dt.datetime.now()).total_seconds() / 3600

        return lat, lon, utc_offset, tz_string

    def get_telugu_year(self,gregorian_year):
        base_year = 1927  # Prabhava
        index = (gregorian_year - base_year) % 60
        return TELUGU_YEAR_NAMES[index]
    
    def compute_tithi(self, moon_sidereal, sun_sidereal, year, month, day, hour, minute, second, utc_offset):
        # Current tithi name
        tithi_angle = (moon_sidereal - sun_sidereal) % 360
        tithi_index = int(tithi_angle // 12)
        tithi_name = TITHI_NAMES[tithi_index]

        # Use transitions to find end time and next tithi
        transitions = self.get_tithi_transitions(year, month, day, hour, minute, second, utc_offset)
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

    def compute_nakshatra(self, abs_lon, jd_ut, utc_offset):
        
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

    def compute_karana(self,moon_sidereal, sun_sidereal):
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

    def compute_yoga(self, moon_sidereal, sun_sidereal):
        yoga_index = int((moon_sidereal + sun_sidereal) % 360 // (360 / 27))
        return YOGA_NAMES[yoga_index]

    def current_karana_yoga_end(self,t0, sidereal_positions):
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

    def get_tithi_transitions(self, year, month, day, hour, minute, second, utc_offset, steps=24):
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
    
    def get_sign_and_abs(self,lon: float):
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


if __name__ == "__main__":

    try:
        PanchangaApp().run()
    except Exception as e:
        print("Error while running PanchangaApp:", e)
        traceback.print_exc()