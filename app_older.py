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
import pytz
import swisseph as swe
import mobile_main_working_fine as engine
import traceback

# Import your engine functions
# from mobile_main import lookup_city, generate_birth_chart,compute_julian_day, get_sidereal_positions 

""" def format_dms(degrees_float):
    degrees = int(degrees_float)
    minutes_float = (degrees_float - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return f"{degrees}°{minutes:02d}'{seconds:05.2f}\""
"""
""" def get_sign_name(sign_index):
    signs = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
    return signs[sign_index % 12] """

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
        form.add_widget(Label(text="TOB (HH:MM)", size_hint_y=None, height=30))
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
    
    def on_save_pdf(self, *_):
        try:
            preview_text = self.output_label.text

            if not preview_text.strip():
                self.output_label.text += "\n\n⚠️ Nothing to save yet. Generate Birth Chart first."
                return

            filename = "birth_chart_output.pdf"
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Title formatting
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, height - 50, self.title_label.text)

            # Reset font for body
            c.setFont("Helvetica", 11)

            # Write text line by line
            y = height - 80
            for line in preview_text.split("\n"):
                if line.strip().startswith("**BIRTH CHART"):
                    c.setFont("Helvetica-Bold", 13)
                elif line.strip().endswith(":") or "Details" in line:
                    c.setFont("Helvetica-Bold", 12)
                else:
                    c.setFont("Helvetica", 11)

                c.drawString(50, y, line)
                y -= 15

                # New page if needed
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = height - 50

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

    def on_generate(self, *_):
        try:
            # Collect inputs
            name = self.name_input.text.strip()
            city = self.city_input.text.strip()
            dob_str = self.dob_input.text.strip()
            tob_str = self.tob_input.text.strip()

            # Parse DOB and TOB for preview only
            dob = dt.datetime.strptime(dob_str, "%Y-%m-%d").date()
            tob = dt.datetime.strptime(tob_str, "%H:%M").time()

            # Lookup city details via mobile_main
            lat, lon, utc_offset, tz_string = mobile_main.lookup_city(city)
            tz = pytz.timezone(tz_string)
            mobile_main.ist_tz = tz  # ensure global IST TZ used by format_end_time

            print("DEBUG lookup_city:", lat, lon, utc_offset, tz_string)

            # Ensure TOB has seconds for julian calculation
            if len(tob_str.split(":")) == 2:
                tob_str = tob_str + ":00"

            # JD and sidereal positions
            jd_ut = mobile_main.compute_julian_day(dob_str, tob_str, utc_offset)

            # Use the constants defined in your module; pass lat/lon so Ascendant is included
            flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
            sidereal_positions = mobile_main.get_sidereal_positions(jd_ut, flags=flags, lat=lat, lon=lon)

            # Build full chart dict using legacy functions
            chart_dict = mobile_main.generate_birth_chart(
                name=name,
                dob=dob_str,
                tob=tob_str,
                city=city,
                lat=lat,
                lon=lon,
                utc_offset=utc_offset,
                jd_ut=jd_ut,
                sidereal_positions=sidereal_positions,
                tz_string=tz_string
            )

            print("DEBUG sidereal_positions keys:", list(sidereal_positions.keys()))
            print("DEBUG sidereal_positions sample:", sidereal_positions.get("Moon"))

            # ---------------- PREVIEW BLOCK ----------------
            preview = []
            preview.append(f"**BIRTH CHART OF {name.upper()}**\n")

            # Birth data
            preview.append("Birth_data:")
            preview.append(f"Name       : {name}")
            preview.append(f"Date       : {dob}")
            preview.append(f"Time       : {tob}")
            preview.append(f"Place      : {city}")
            preview.append(f"Latitude   : {lat}")
            preview.append(f"Longitude  : {lon}")
            preview.append("")

            # Panchanga details
            preview.append("Panchanga Details at Birth:")
            for key in ["WEEKDAY", "TITHI", "TITHI_END", "NAKSHATRA", "NAK_END",
                        "KARANA", "KARANA_END", "YOGA", "YOGA_END", "SUNRISE", "SUNSET"]:
                if key in chart_dict:
                    preview.append(f"{key:12s}: {chart_dict[key]}")
            preview.append("")

            # Planetary positions
            preview.append("Planetary Positions at Birth:")
            preview.append("------------------------------------------------------------")
            preview.append("Planet     | Longitude        | Abs. Longitude | Zodiac Sign")
            preview.append("------------------------------------------------------------")
            for planet, pdata in chart_dict.get("PLANETS", {}).items():
                long_val = pdata.get("LONG") or pdata.get("long") or ""
                sign_val = pdata.get("SIGN") or pdata.get("sign") or ""
                abs_val  = pdata.get("ABS")  or pdata.get("abs")  or ""

                long_str = str(long_val)
                sign_str = str(sign_val)
                abs_str  = f"{abs_val:.4f}" if isinstance(abs_val, (int, float)) else str(abs_val)

                preview.append(f"{planet:10s} | {long_str:15s} | {abs_str:14s} | {sign_str:10s}")

            # Optional: show Ascendant if present
            if "LONG_ASC" in chart_dict:
                preview.append("")
                preview.append(f"Ascendant  : {chart_dict['LONG_ASC']} | {chart_dict.get('ABS_ASC','')} | {chart_dict.get('SIGN_ASC','')}")

            # Display output
            self.output_label.text = "\n".join(preview)
            self.title_label.text = f"Birth chart of {name}"

        except Exception as e:
            self.output_label.text = f"Error: {str(e)}"

class PanchangaApp(App):
    def build(self):
        return PanchangaScreen()

if __name__ == "__main__":
    try:
        PanchangaApp().run()
    except Exception as e:
        print("Error while running PanchangaApp:", e)
        traceback.print_exc()