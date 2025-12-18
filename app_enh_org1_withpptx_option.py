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


class PanchangaApp(App):
   
    def build(self):
        Window.size = (414, 896)

        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        root.canvas.before.clear()
        with root.canvas.before:
            Color(0.95, 0.95, 1, 1)  # uniform light bluish background
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
                color=(0, 0, 0, 1)   # black text
            ))
            input_grid.add_widget(widget)

        # Inputs
        self.name_input = TextInput(hint_text="Name", size_hint=(input_width, None),
                                    height=input_height, background_color=(1,1,1,1),
                                    foreground_color=(0,0,0,1))
        add_input("Name:", self.name_input)

        self.day_spinner = Spinner(text="Day", values=[str(i) for i in range(1, 32)],
                                size_hint=(input_width, None), height=input_height,
                                background_color=(1,1,1,1), color=(0,0,0,1))
        add_input("Day:", self.day_spinner)

        self.month_spinner = Spinner(text="Month", values=[str(i) for i in range(1, 13)],
                                    size_hint=(input_width, None), height=input_height,
                                    background_color=(1,1,1,1), color=(0,0,0,1))
        add_input("Month:", self.month_spinner)

        self.year_input = TextInput(hint_text="Year", size_hint=(input_width, None),
                                    height=input_height, background_color=(1,1,1,1),
                                    foreground_color=(0,0,0,1))
        add_input("Year:", self.year_input)

        self.city_input = TextInput(hint_text="City", size_hint=(input_width, None),
                                    height=input_height, background_color=(1,1,1,1),
                                    foreground_color=(0,0,0,1))
        add_input("City:", self.city_input)

        # Time row: Hour, Minute, Second side-by-side
        time_box = BoxLayout(orientation='horizontal', spacing=5,
                            size_hint_y=None, height=input_height)

        self.hour_spinner = Spinner(text="Hour", values=[f"{i:02d}" for i in range(0,24)],
                                    size_hint=(0.1, None), height=input_height,
                                    background_color=(1,1,1,1), color=(0,0,0,1))
        self.minute_spinner = Spinner(text="Minute", values=[f"{i:02d}" for i in range(0,60)],
                                    size_hint=(0.1, None), height=input_height,
                                    background_color=(1,1,1,1), color=(0,0,0,1))
        self.second_spinner = Spinner(text="Second", values=[f"{i:02d}" for i in range(0,60)],
                                    size_hint=(0.1, None), height=input_height,
                                    background_color=(1,1,1,1), color=(0,0,0,1))

        time_box.add_widget(Label(text="Time:", size_hint=(0.15, None),
                                height=input_height, color=(0,0,0,1)))
        time_box.add_widget(self.hour_spinner)
        time_box.add_widget(self.minute_spinner)
        time_box.add_widget(self.second_spinner)

        root.add_widget(input_grid)
        root.add_widget(time_box)

        # Buttons row
        button_font_size = 16
        button_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=45, spacing=8, padding=(20, 0))

        generate_btn = Button(text="Generate", size_hint_x=0.2, font_size=button_font_size)
        save_btn = Button(text="Save PDF", size_hint_x=0.2, font_size=button_font_size)
        exit_btn = Button(text="Exit", size_hint_x=0.2, font_size=button_font_size)
        reset_btn = Button(text="Reset", size_hint_x=0.2, font_size=button_font_size)

        generate_btn.bind(on_press=self.on_generate)
        save_btn.bind(on_press=self.on_save_pdf)
        exit_btn.bind(on_press=lambda *args: App.get_running_app().stop())
        reset_btn.bind(on_press=self.on_reset)

        button_box.add_widget(generate_btn)
        button_box.add_widget(save_btn)
        button_box.add_widget(exit_btn)
        button_box.add_widget(reset_btn)

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
            color=(0, 0, 0, 1)   # black text
        )
        self.output_label.bind(
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        return root

    def on_reset(self, instance):
        self.name_input.text = ""
        self.day_spinner.text = "Day"
        self.month_spinner.text = "Month"
        self.year_input.text = ""
        self.city_input.text = ""
        self.hour_input.text = ""
        self.minute_input.text = ""
        self.second_input.text = ""
        self.output_label.text = ""



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
    
    
    def on_save_pdf(self, instance):
        """Save the generated chart output into a PDF file."""
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

            # Title: BIRTH CHART OF {NAME} (Helvetica-Bold, 14, uppercase)
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

            c.save()

            # Confirmation in widget (black text on uniform background)
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