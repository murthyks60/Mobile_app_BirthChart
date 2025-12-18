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
import mobile_main_working_fine as engine
import traceback
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

SIGNS = {
    0:"Ar", 1:"Ta", 2:"Ge", 3:"Cn",
    4:"Le", 5:"Vi", 6:"Li", 7:"Sc",
    8:"Sg", 9:"Cp", 10:"Aq", 11:"Pi"
}

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


class PanchangaApp(App):
   
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

        self.day_spinner = Spinner(
            text="Day", values=[str(i) for i in range(1, 32)],
            size_hint=(input_width, None), height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )
        add_input("Day:", self.day_spinner)

        self.month_spinner = Spinner(
            text="Month", values=[str(i) for i in range(1, 13)],
            size_hint=(input_width, None), height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )
        add_input("Month:", self.month_spinner)

        self.year_input = TextInput(
            hint_text="Year", size_hint=(input_width, None), height=input_height,
            background_normal="", background_color=(0.95, 0.95, 1, 1),
            foreground_color=(0, 0, 0, 1)
        )
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
            text="Hour", values=[f"{i:02d}" for i in range(0,24)],
            size_hint=(0.1, None), height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )
        self.minute_spinner = Spinner(
            text="Minute", values=[f"{i:02d}" for i in range(0,60)],
            size_hint=(0.1, None), height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )
        self.second_spinner = Spinner(
            text="Second", values=[f"{i:02d}" for i in range(0,60)],
            size_hint=(0.1, None), height=input_height,
            background_normal="", background_down="",
            background_color=(0.95, 0.95, 1, 1), color=(0,0,0,1)
        )

        time_box.add_widget(Label(text="Time:", size_hint=(0.15, None),
                                height=input_height, color=(1,1,1,1)))
        time_box.add_widget(self.hour_spinner)
        time_box.add_widget(self.minute_spinner)
        time_box.add_widget(self.second_spinner)

        root.add_widget(input_grid)
        root.add_widget(time_box)

        # Buttons row (only 4 buttons now)
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

        generate_btn.bind(on_press=self.on_generate)
        save_pdf_btn.bind(on_press=self.on_save_pdf)
        reset_btn.bind(on_press=self.on_reset)
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

    def on_reset(self, instance):
        self.name_input.text = ""
        self.city_input.text = ""
        self.year_input.text = ""
        self.day_spinner.text = "Day"
        self.month_spinner.text = "Month"
        self.hour_spinner.text = "Hour"
        self.minute_spinner.text = "Minute"
        self.second_spinner.text = "Second"
        self.output_label.text = ""
        self.output_label.color = (0, 0, 0, 1)  # keep text visible
 
    def on_save_pptx(self, instance):
        try:
            # Collect inputs
            name = self.name_input.text.strip()
            city = self.city_input.text.strip()
            dob = f"{self.year_input.text}-{int(self.month_spinner.text):02d}-{int(self.day_spinner.text):02d}"
            tob = f"{self.hour_spinner.text}:{self.minute_spinner.text}:{self.second_spinner.text}"

            # Generate chart silently
            chart = engine.generate_birth_chart(name, dob, tob, city)

            # Call a separate PPTX function (no input prompt)
            filename = engine.populate_pptx(chart)

            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text += f"\n\nPPTX saved as {filename}"

        except Exception as e:
            import traceback
            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text += f"\n\nError saving PPTX: {e}\n{traceback.format_exc()}"

    def _update_rect(self, instance, value):
        """Keep background rectangle aligned with window size."""
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def on_generate(self, *_):
        try:
            # Collect inputs
            name = self.name_input.text.strip()
            city = self.city_input.text.strip()

            # Use spinner values for DOB, text inputs for Year
            dob = f"{self.year_input.text}-{int(self.month_spinner.text):02d}-{int(self.day_spinner.text):02d}"

            # Use spinner values for TOB
            tob = f"{self.hour_spinner.text}:{self.minute_spinner.text}:{self.second_spinner.text}"

            # Lookup city
            lat, lon, utc_offset, tz_string = engine.lookup_city(city)
            tz = pytz.timezone(tz_string)
            engine.tz = tz

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
            chart = engine.generate_birth_chart(
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

        except Exception as e:
            import traceback
            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text += f"\n\nError generating chart: {e}\n{traceback.format_exc()}"
       
    def cell_bounds(row, col, x, y, step):
        left = x + col * step
        right = left + step
        pdf_row = 3 - row  # flip for PDF coords
        bottom = y + pdf_row * step
        top = bottom + step
        return left, bottom, right, top

    def get_sign_from_longitude(self, longitude):
        for sign, (low, high) in SIGN_RANGES.items():
            if low <= longitude <= high:
                return sign
        return ""

    def draw_rasi_chakra(self, c, x, y, size, chart):
        """
        South Indian Rāśi Chakra rendered as a 4×4 ReportLab Table:
        - Each cell: Sign + stacked planets via Paragraph (<br/>).
        - Only central blanks are spanned across columns 1–2.
        - No pixel math for text coordinates.
        """

        # Each cell is step × step
        step = size / 4.0

        # Fixed 4×4 grid with blanks in the center (Table 2 layout)
        house_grid = {
            (0,0): 11, (0,1): 0,  (0,2): 1,  (0,3): 2,
            (1,0): 10, (1,1): "", (1,2): "", (1,3): 3,
            (2,0): 9,  (2,1): "", (2,2): "", (2,3): 4,
            (3,0): 8,  (3,1): 7,  (3,2): 6,  (3,3): 5
        }

        signs = chart.get("SIGNS", {})
        # Build planets by sign
        planet_positions = {}
        for planet, lon in chart.get("PLANETS", {}).items():
            sign = self.get_sign_from_longitude(lon)
            planet_positions.setdefault(sign, []).append(planet)

        # Styles
        styles = getSampleStyleSheet()
        cell_style_left = ParagraphStyle(
            'CellLeft',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            alignment=0,   # LEFT
            spaceBefore=0,
            spaceAfter=0,
        )
        center_label_style = ParagraphStyle(
            'CenterLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            alignment=1,   # CENTER
        )
        center_small_style = ParagraphStyle(
            'CenterSmall',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            alignment=1,   # CENTER
        )

        # Build 4×4 data grid with Paragraphs (do not use plain strings)
        data = []
        for row in range(4):
            row_data = []
            for col in range(4):
                house = house_grid[(row, col)]
                if house == "":
                    # Central blanks will be spanned; place content only in (1,1) and (2,1)
                    if row == 1 and col == 1:
                        row_data.append(Paragraph("RĀŚI CHAKRA", center_label_style))
                    elif row == 2 and col == 1:
                        dob = chart.get("DATE", "")
                        tob = chart.get("TIME", "")
                        row_data.append(Paragraph(f"DOB: {dob}<br/>TOB: {tob}", center_small_style))
                    else:
                        row_data.append(Paragraph("", cell_style_left))
                else:
                    sign = signs.get(house, "")
                    planets = planet_positions.get(sign, [])
                    text = sign if not planets else (sign + "<br/>" + "<br/>".join(planets))
                    row_data.append(Paragraph(text, cell_style_left))
            data.append(row_data)

        # Ensure true 4 columns × 4 rows
        col_widths = [step, step, step, step]
        row_heights = [step, step, step, step]
        table = Table(data, colWidths=col_widths, rowHeights=row_heights)

        # Style: grid, paddings, and spans for central blanks (across columns 1–2)
        # Coordinates are (col, row): (1,1)→(2,1) and (1,2)→(2,2)
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),

            # Global paddings for clean margins
            ('LEFTPADDING',  (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING',   (0,0), (-1,-1), 3),
            ('BOTTOMPADDING',(0,0), (-1,-1), 3),

            # Top-left alignment for zodiac cells
            ('ALIGN',  (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),

            # Central spans (merge two columns only in rows 1 and 2)
            ('SPAN', (1,1), (2,1)),  # row=1: RĀŚI CHAKRA across col 1–2
            ('SPAN', (1,2), (2,2)),  # row=2: DOB/TOB across col 1–2

            # Center alignment for the merged central cells
            ('ALIGN',  (1,1), (2,1), 'CENTER'),
            ('VALIGN', (1,1), (2,1), 'MIDDLE'),
            ('ALIGN',  (1,2), (2,2), 'CENTER'),
            ('VALIGN', (1,2), (2,2), 'MIDDLE'),
        ]))

        # Draw table
        table.wrapOn(c, x, y)
        table.drawOn(c, x, y)

    def on_save_pdf(self, instance):
        """Save the generated chart output into a PDF file with Rasi Chakra."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            # Collect inputs again (so PDF matches widget)
            name = self.name_input.text.strip()
            city = self.city_input.text.strip()
            dob = f"{self.year_input.text}-{int(self.month_spinner.text):02d}-{int(self.day_spinner.text):02d}"
            tob = f"{self.hour_spinner.text}:{self.minute_spinner.text}:{self.second_spinner.text}"

            # Lookup city
            lat, lon, utc_offset, tz_string = engine.lookup_city(city)
            tz = pytz.timezone(tz_string)
            engine.tz = tz

            # Datetime
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
            chart = engine.generate_birth_chart(
                name, dob, tob, city, lat, lon, utc_offset,
                jd_ut, sidereal_positions
            )

            # Clean Telugu Year string
            telugu_year = chart.get("TELUGU_YEAR", "").replace("(", "").replace(")", "")

            # Timestamped PDF file name
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.pdf"

            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Title: ceremonial
            title = f"BIRTH CHART OF {name.upper()}"
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width / 2, height - 50, title)

            # Info section
            c.setFont("Courier", 10)
            y = height - 80
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
                ("YOGA_END", chart.get("YOGA_END", ""))
            ]
            for lbl, val in info_fields:
                c.drawString(50, y, f"{lbl:<16} : {val}")
                y -= 15

            # Planet positions
            y -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "PLANET POSITIONS")
            y -= 15
            c.setFont("Courier", 10)
            c.drawString(50, y, f"{'Planet':<12}{'Longitude':<20}{'ABS.Longitude':<15}{'Sign':<5}")
            y -= 15

            planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu", "Ascendant"]

            for planet in planets:
                prefix = planet[:2] if planet != "Ascendant" else "Asc"
                long_val = chart.get(f"LONG_{prefix}", "")
                abs_val  = chart.get(f"ABS_{prefix}", "")
                sign_val = chart.get(f"SIGN_{prefix}", "")
                c.drawString(50, y, f"{planet:<12}{long_val:<20}{abs_val:<15}{sign_val:<5}")
                y -= 15
                if y < 50:
                    c.showPage()
                    c.setFont("Courier", 10)
                    y = height - 50

            # --- NEW: Draw Rasi Chakra (Table 2 layout) ---
            self.draw_rasi_chakra(c, x=340, y=570, size=200, chart=chart)

            c.save()

            # Confirmation in widget
            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text += f"\n\nPDF saved as {filename}"

        except Exception as e:
            import traceback
            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text += f"\n\nError saving PDF: {e}\n{traceback.format_exc()}"
   
    def _update_rect(self, instance, value):
        """Keep background rectangle aligned with window size."""
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def on_exit(self, *_):
        """Gracefully stop the app when Exit button is pressed."""
        from kivy.app import App
        App.get_running_app().stop()

    def _update_text_height(self, instance, value):
        instance.height = instance.texture_size[1]
        instance.text_size = (self.output_scroll.width - 20, None)

if __name__ == "__main__":
    try:
        PanchangaApp().run()
    except Exception as e:
        print("Error while running PanchangaApp:", e)
        traceback.print_exc()