from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.screenmanager import FadeTransition, NoTransition

Config.set("graphics", "width", 400)
Config.set("graphics", "height", 800)

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.lang.builder import Builder

from kivymd.uix.screenmanager import MDScreenManager
from kivy.graphics.context_instructions import Color
from kivymd.uix.boxlayout import MDBoxLayout


class HomeBotRootWidget(MDBoxLayout):
    def __init__(self, **kwargs):
        super(HomeBotRootWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.switch_home, 6)

    def switch_home(self, *args):
        self.ids.screen_manager.transition = NoTransition()
        self.ids.screen_manager.current = "home_page"


class HomeBotApp(MDApp):
    def __init__(self, **kwargs):
        super(HomeBotApp, self).__init__(**kwargs)

    def load_kv_files(self):
        Builder.load_file("main.kv")
        Builder.load_file("home_page.kv")

    def build(self):
        self.load_kv_files()
        return HomeBotRootWidget()


if __name__ == "__main__":
    HomeBotApp().run()
