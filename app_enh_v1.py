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
planet_abbr = {
    "Ascendant": "Asc",
    "Sun": "Su",
    "Moon": "Mo",
    "Mercury": "Me",
    "Venus": "Ve",
    "Mars": "Ma",
    "Jupiter": "Ju",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke"
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
    def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.chart_data = None

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

    def on_save_pdf(self, *_):
        """Save the generated chart output into a PDF file."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors

            # Helper: safely get text from spinner or text input
            def get_text(attr_candidates, label):
                for attr in attr_candidates:
                    if hasattr(self, attr):
                        return getattr(self, attr).text.strip()
                raise AttributeError(f"Missing {label} input (expected one of {attr_candidates})")

            # Collect inputs (adjust candidate names to match your actual widget IDs)
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
            lat, lon, utc_offset, tz_string = engine.lookup_city(city)
            tz = pytz.timezone(tz_string)
            engine.tz = tz

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

            chart = engine.generate_birth_chart(
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
            title = f"Birth Chart for {name}"
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width / 2, height - 50, title)

            # Section 1: Birth Data – Panchangam Details
            y = height - 90
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "BIRTH DATA – PANCHANGAM DETAILS")
            y -= 20

            c.setFont("Courier", 10)
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
                c.drawString(50, y, f"{lbl:<16} : {val}")
                y -= 15

            # Section 3: Rāśi Chakra Diagram
            chart_x = 330   # right side start
            chart_y = height - 310   # align vertically with Table 1
            chart_size = 250
            self.draw_south_indian_chart(c, chart_x, chart_y, 220, sidereal_positions, dob, tob)
            # Section 2: Planet Positions (Table 3 title)
            y -= 30  # spacing after info block
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "PLANET POSITIONS")
            y -= 25  # gap below title before table

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
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('FONTNAME', (0,0), (-1,-1), 'Courier'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
            ]))
            # Wrap to get actual width
            table3_width, table3_height = table.wrap(0, 0)

            # Compute centered x
            x_center = (width - table3_width) / 2

            # Draw table centered
            table.drawOn(c, x_center, y - table3_height)



            c.save()
            self.output_label.text += f"\n\nPDF saved as {filename}"

        except Exception as e:
            import traceback
            self.output_label.text += f"\n\nError saving PDF: {e}\n{traceback.format_exc()}"
    
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
            # Display in widget (black text on uniform background)

            # Save chart data for PPTX generation
            self.chart_data = chart

            # Trigger PPTX (and optional PDF) generation
      
        except Exception as e:
            import traceback
            self.output_label.color = (0, 0, 0, 1)
            self.output_label.text += f"\n\nError generating chart: {e}\n{traceback.format_exc()}"

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

    def draw_south_indian_chart(self, c, x, y, size, sidereal_positions, dob, tob):
        """Draw South Indian 4x4 Rāśi Chakra with merged cells and stacked planets."""
        cell = size / 4

        # Draw horizontal lines
        for i in range(5):
            c.line(x, y + i*cell, x + size, y + i*cell)

        # Draw vertical lines, skipping merges
        for j in range(5):
            if j == 2:
                c.line(x + j*cell, y, x + j*cell, y + cell)       # bottom
                c.line(x + j*cell, y + 2*cell, x + j*cell, y + size)  # top
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
            rasi_index = int(lon // 30)
            rasi = rasi_names[rasi_index]
            if rasi in rasi_planets:
                abbr = planet_abbr.get(planet, planet[:2])  # fallback to first 2 letters
                rasi_planets[rasi].append(abbr)


        # Draw rāśi labels
        c.setFont("Helvetica-Bold", 8)
        for rasi, (row,col) in rasi_order.items():
            rx = x + col*cell
            ry = y + (3-row)*cell
            c.drawString(rx+2, ry+cell-10, rasi)

        # Draw stacked planets
        c.setFont("Courier", 8)
        for rasi, planets in rasi_planets.items():
            if rasi in rasi_order:
                row, col = rasi_order[rasi]
                rx = x + col*cell
                ry = y + (3-row)*cell
                for i, planet in enumerate(planets):
                    c.drawString(rx+10, ry+cell/2 - 5*i, planet)

        # Draw Ascendant
        asc_lon = sidereal_positions.get("Ascendant", 0)
        asc_rasi = rasi_names[int(asc_lon // 30)]
        if asc_rasi in rasi_order:
            row, col = rasi_order[asc_rasi]
            rx = x + col*cell
            ry = y + (3-row)*cell
            c.setFont("Helvetica-Bold", 8)
            c.drawString(rx+10, ry+cell/2 + 10, "Asc")

        # Merged cell: RASI CHAKRA
        rx = x + cell
        ry = y + 2*cell
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(rx + cell, ry + cell/2, "RASI CHAKRA")

        # Merged cell: DOB / TOB
        rx = x + cell
        ry = y + cell
        c.setFont("Courier", 8)
        c.drawCentredString(rx + cell, ry + cell/2 + 5, f"DOB: {dob}")
        c.drawCentredString(rx + cell, ry + cell/2 - 5, f"TOB: {tob}")
if __name__ == "__main__":
    try:
        PanchangaApp().run()
    except Exception as e:
        print("Error while running PanchangaApp:", e)
        traceback.print_exc()