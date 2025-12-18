# app.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import datetime as dt
import swisseph as swe
import mobile_main_working_fine as engine
import traceback


class PanchangaScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 10

        # Title (dynamic, centered and bold)
        self.title_label = Label(
            text="Birth Chart",
            font_size='22sp',
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=50
        )
        self.title_label.bind(size=lambda *args: setattr(self.title_label, 'text_size', self.title_label.size))
        self.add_widget(self.title_label)

        # Input form layout
        form = GridLayout(cols=2, spacing=8, size_hint=(1, None))
        form.bind(minimum_height=form.setter('height'))

        # Name
        form.add_widget(Label(text="Name", size_hint_y=None, height=30))
        self.name_input = TextInput(text="KS Murthy", multiline=False, size_hint_y=None, height=30)
        form.add_widget(self.name_input)

        # City
        form.add_widget(Label(text="City", size_hint_y=None, height=30))
        self.city_input = TextInput(text="Chirala", multiline=False, size_hint_y=None, height=30)
        form.add_widget(self.city_input)

        # DOB
        form.add_widget(Label(text="DOB (YYYY-MM-DD)", size_hint_y=None, height=30))
        self.dob_input = TextInput(text="1960-10-07", multiline=False, size_hint_y=None, height=30)
        form.add_widget(self.dob_input)

        # TOB
        form.add_widget(Label(text="TOB (HH:MM or HH:MM:SS)", size_hint_y=None, height=30))
        self.tob_input = TextInput(text="01:50", multiline=False, size_hint_y=None, height=30)
        form.add_widget(self.tob_input)

        self.add_widget(form)

        # Action buttons
        btn_row = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, None), height=50)

        self.generate_btn = Button(text="Generate Birth Chart")
        self.generate_btn.bind(on_press=self.on_generate)
        btn_row.add_widget(self.generate_btn)

        self.save_pdf_btn = Button(text="Save as PDF")
        self.save_pdf_btn.bind(on_press=self.on_save_pdf)
        btn_row.add_widget(self.save_pdf_btn)

        self.exit_btn = Button(text="Exit")
        self.exit_btn.bind(on_press=self.on_exit)
        btn_row.add_widget(self.exit_btn)

        self.add_widget(btn_row)

        # Output area (scrollable)
        self.output_scroll = ScrollView(size_hint=(1, 1))
        self.output_label = Label(
            text="",
            size_hint_y=None,
            valign='top'
        )
        self.output_label.bind(texture_size=self._update_text_height)
        self.output_scroll.add_widget(self.output_label)
        self.add_widget(self.output_scroll)

    def _normalize_time(self, tob_text: str) -> str:
        """Normalize TOB to HH:MM:SS without changing engine code."""
        s = tob_text.strip()
        parts = s.split(":")
        if len(parts) == 2:
            h, m = parts
            return f"{int(h):02d}:{int(m):02d}:00"
        elif len(parts) == 3:
            h, m, sec = parts
            return f"{int(h):02d}:{int(m):02d}:{int(sec):02d}"
        else:
            raise ValueError(f"Invalid TOB format (expected HH:MM or HH:MM:SS): {tob_text}")

    
    def on_generate(self, *_):
        """Collect input values, replicate __main__ pipeline, and generate chart with fixed-width formatted output."""
        try:
            # 1) Read UI inputs and normalize TOB
            name = self.name_input.text.strip()
            dob  = self.dob_input.text.strip()
            tob_raw = self.tob_input.text.strip()
            parts = tob_raw.split(":")
            if len(parts) == 2:
                h, m = parts
                tob = f"{int(h):02d}:{int(m):02d}:00"
            elif len(parts) == 3:
                h, m, s = parts
                tob = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            else:
                raise ValueError(f"Invalid TOB format: {tob_raw}")
            city = self.city_input.text.strip()

            # 2) Lookup city and inject tz into engine
            lat, lon, utc_offset, tz_string = engine.lookup_city(city)
            import pytz
            tz = pytz.timezone(tz_string)
            engine.tz = tz

            # 3) Convert DOB+TOB into datetime
            import datetime as dt
            dob_obj = dt.datetime.strptime(dob, "%Y-%m-%d").date()
            tob_obj = dt.datetime.strptime(tob, "%H:%M:%S").time()
            dt_obj  = dt.datetime.combine(dob_obj, tob_obj)

            # 4) Compute Julian Day and sidereal positions
            import swisseph as swe
            jd_local = swe.julday(
                dt_obj.year, dt_obj.month, dt_obj.day,
                dt_obj.hour + dt_obj.minute/60 + dt_obj.second/3600,
                swe.GREG_CAL
            )
            jd_ut = jd_local - (utc_offset / 24.0)
            swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

            def calc_lon(body):
                return swe.calc_ut(jd_ut, body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]

            sun_lon     = calc_lon(swe.SUN)
            moon_lon    = calc_lon(swe.MOON)
            mars_lon    = calc_lon(swe.MARS)
            mercury_lon = calc_lon(swe.MERCURY)
            jupiter_lon = calc_lon(swe.JUPITER)
            venus_lon   = calc_lon(swe.VENUS)
            saturn_lon  = calc_lon(swe.SATURN)
            rahu_lon    = calc_lon(swe.MEAN_NODE)
            ketu_lon    = (rahu_lon + 180) % 360

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

            # 5) Generate chart
            chart = engine.generate_birth_chart(
                name, dob, tob, city, lat, lon, utc_offset,
                jd_ut,
                sidereal_positions
            )

            # 6) Fixed-width formatting for widget
            import os
            mono_path_candidates = [
                r"C:\Windows\Fonts\consola.ttf",
                r"C:\Windows\Fonts\Courier.ttf",
                r"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                r"/System/Library/Fonts/Monaco.ttf"
            ]
            mono_font = next((p for p in mono_path_candidates if os.path.exists(p)), None)
            if mono_font:
                self.output_label.font_name = mono_font

            line_sep_40 = "=" * 40
            line_sep_56 = "=" * 56

            # Info section
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

            self.output_label.text = "\n".join(output_lines)

        except Exception as e:
            import traceback
            self.output_label.text += f"\n\nError generating chart: {e}\n{traceback.format_exc()}"
    
    def on_save_pdf(self, *_):
        try:
            preview_text = self.output_label.text
            if not preview_text.strip():
                self.output_label.text += "\n\n⚠️ Nothing to save yet. Generate Birth Chart first."
                return

            filename = "birth_chart_output.pdf"
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Use monospaced font for perfect alignment
            c.setFont("Courier-Bold", 16)
            c.drawCentredString(width / 2, height - 50, self.title_label.text)

            y = height - 80

            def draw_line(line, bold=False):
                nonlocal y
                c.setFont("Courier-Bold" if bold else "Courier", 11)
                c.drawString(50, y, line)
                y -= 15
                if y < 50:
                    c.showPage()
                    c.setFont("Courier", 11)
                    y = height - 50

            for line in preview_text.split("\n"):
                stripped = line.strip()
                if stripped.startswith("📋") or stripped.startswith("PLANET POSITIONS"):
                    draw_line(line, bold=True)
                elif stripped.startswith("="):
                    draw_line(line, bold=False)
                elif ":" in line and "|" not in line:
                    label, value = line.split(":", 1)
                    fw_line = f"{label.strip():<16} : {value.strip()}"
                    draw_line(fw_line, bold=False)
                else:
                    draw_line(line, bold=False)

            c.save()
            self.output_label.text += f"\n\n✅ Saved as PDF: {filename}"

        except Exception as e:
            self.output_label.text += f"\n\nError saving PDF: {e}"

    def on_exit(self, *_):
        from kivy.app import App
        App.get_running_app().stop()

    def _update_text_height(self, instance, value):
        self.output_label.height = value[1]
        self.output_label.text_size = (self.output_scroll.width - 20, None)


class PanchangaApp(App):
    def build(self):
        return PanchangaScreen()


if __name__ == "__main__":
    try:
        PanchangaApp().run()
    except Exception as e:
        print("Error while running PanchangaApp:", e)
        traceback.print_exc()