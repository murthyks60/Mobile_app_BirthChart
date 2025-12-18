from kivy.app import App
from kivy.uix.label import Label
from birth_chart_engine import generate_birth_chart
import datetime as dt


# df = pd.read_excel("worldcities_with_timezone.xlsx")
#    lat, lon, utc_offset,tz_offset = lookup_city(city, df)


class BirthChartApp(App):
    def build(self):
        dob = dt.date(1960, 10, 8)
        tob = dt.time(6, 20)
        city = "Vijayawada"
        chart = generate_birth_chart("Test User", dob, tob, city)
        return Label(text=str(chart))

if __name__ == "__main__":
    BirthChartApp().run()