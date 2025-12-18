from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.core.text import LabelBase
import os

# PDF export
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import app_enh
from app_enh import PanchangaApp


# Register a monospaced font explicitly (adjust path if needed)
LabelBase.register(name="Mono", fn_regular=r"C:\Windows\Fonts\consola.ttf")

class PanchangaForm(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=8, **kwargs)

        with self.canvas.before:
            Color(0.8, 0.9, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.add_widget(Label(text="Birth Data Form", color=(0, 0, 0, 1),
                              size_hint_y=None, height=30, font_size=20))

        # Name row
        name_row = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=30)
        name_row.add_widget(Label(text="Name", size_hint_x=None, width=100, color=(0, 0, 0, 1)))
        self.name_input = TextInput(hint_text="Enter Name", multiline=False)
        name_row.add_widget(self.name_input)
        self.add_widget(name_row)

        # DOB row
        dob_row = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=30)
        dob_row.add_widget(Label(text="DOB", size_hint_x=None, width=100, color=(0, 0, 0, 1)))
        self.day_spinner = Spinner(text="Day", values=[str(d) for d in range(1, 32)], size_hint_x=None, width=60)
        self.month_spinner = Spinner(text="Mon", values=[str(m) for m in range(1, 13)], size_hint_x=None, width=60)
        self.year_input = TextInput(hint_text="Year", multiline=False, size_hint_x=None, width=80)
        dob_row.add_widget(self.day_spinner)
        dob_row.add_widget(self.month_spinner)
        dob_row.add_widget(self.year_input)
        self.add_widget(dob_row)

        # TOB row
        tob_row = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=30)
        tob_row.add_widget(Label(text="TOB", size_hint_x=None, width=100, color=(0, 0, 0, 1)))
        self.hour_spinner = Spinner(text="Hour", values=[str(h) for h in range(0, 24)], size_hint_x=None, width=60)
        self.minute_spinner = Spinner(text="Min", values=[str(m) for m in range(0, 60)], size_hint_x=None, width=60)
        self.second_spinner = Spinner(text="Sec", values=[str(s) for s in range(0, 60)], size_hint_x=None, width=60)
        tob_row.add_widget(self.hour_spinner)
        tob_row.add_widget(self.minute_spinner)
        tob_row.add_widget(self.second_spinner)
        self.add_widget(tob_row)

        # Place row
        place_row = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=30)
        place_row.add_widget(Label(text="Place of Birth", size_hint_x=None, width=100, color=(0, 0, 0, 1)))
        self.city_input = TextInput(hint_text="City", multiline=False)
        place_row.add_widget(self.city_input)
        self.add_widget(place_row)

        # Buttons
        btn_row = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        gen_btn = Button(text="Generate Chart", background_color=(0.2, 0.8, 0.2, 1), size_hint_x=None, width=150)
        gen_btn.bind(on_press=self.show_dummy_output)
        btn_row.add_widget(gen_btn)

        pdf_btn = Button(text="Make PDF", background_color=(0.2, 0.8, 0.2, 1), size_hint_x=None, width=150)
        pdf_btn.bind(on_press=self.on_save_pdf)
        btn_row.add_widget(pdf_btn)

        exit_btn = Button(text="Exit", background_color=(0.2, 0.8, 0.2, 1), size_hint_x=None, width=100)
        exit_btn.bind(on_press=lambda *_: App.get_running_app().stop())
        btn_row.add_widget(exit_btn)

        self.add_widget(btn_row)

        # Output area
        self.output_scroll = ScrollView(size_hint=(1, 1))
        self.output_label = Label(
            text="",
            halign="left",
            valign="top",
            size_hint_y=None,
            color=(0, 0, 0, 1),
            font_name="Mono",
            font_size=14,
        )
        self.output_label.bind(texture_size=self._update_text_height)
        self.output_scroll.bind(width=self._update_text_width)
        self.output_scroll.add_widget(self.output_label)
        self.add_widget(self.output_scroll)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_text_width(self, instance, value):
        self.output_label.text_size = (self.output_scroll.width - 20, None)
        self.output_label.texture_update()

    def _update_text_height(self, instance, value):
        instance.height = instance.texture_size[1]

    def show_dummy_output(self, *_):
        # Create an instance of PanchangaApp from app_enh
        app = app_enh.PanchangaApp()
        app.on_generate(self)   # call its method, passing your widget
        self._update_text_width(self.output_scroll, self.output_scroll.width)

    def on_save_pdf(self, *_):
        app = app_enh.PanchangaApp()
        app.on_save_pdf(self)



class PanchangaApp(App):
    def build(self):
        return PanchangaForm()
# Simple test harness to pre-fill inputs

if __name__ == "__main__":
    PanchangaApp().run()