import random

from kivy.clock import Clock
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.factory import Factory
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, OptionProperty, ColorProperty
from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.effects.stiffscroll import StiffScrollEffect
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCard, MDSeparator
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelThreeLine, MDExpansionPanelOneLine
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.behaviors.elevation import CommonElevationBehavior
from kivymd.uix.button import MDIconButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.slider import MDSlider

from template_strings import *



class CustomExpansionPanel(MDCard):
    text = StringProperty("")
    content = ObjectProperty(Widget())
    panel_state = OptionProperty("closed", options=["opened", "closed"])

    def __init__(self, text="", content=MDFlatButton(text="test"), panel_state="closed", **kwargs):
        super(CustomExpansionPanel, self).__init__(**kwargs)
        self.text = text
        self.content = content
        self.panel_state = panel_state
        self.separator = Builder.load_string(seperator)

    def update_panel(self):
        self.panel_state = "opened" if self.panel_state == "closed" else "closed"

    def expand(self, *args):
        self.add_widget(self.separator)
        self.add_widget(self.content)
        # self.ids.icon_button.finish_ripple()
        # self.ids.icon_button.start_ripple()

    def close(self, *args):
        self.remove_widget(self.separator)
        self.remove_widget(self.content)
        # self.ids.icon_button.finish_ripple()
        # self.ids.icon_button.start_ripple()

    def on_panel_state(self, *args):
        if self.panel_state == "opened":
            Clock.schedule_once(self.expand)
        else:
            Clock.schedule_once(self.close)


class BaseCard(MDCard):
    def __init__(self, **kwargs):
        super(BaseCard, self).__init__(**kwargs)


class HouseListItem(MDCard):
    gadget = ObjectProperty()

    def __init__(self, gadget, **kwargs):
        self.gadget = gadget
        super(HouseListItem, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_switch_color, 1/20)

    def update_switch_color(self, dt):
        switch = self.ids.switch
        switch.thumb_color_active = "#B6B6B6" if self.gadget.parent_off() else "#2196F3"
        switch.track_color_active = "#DBDBDB" if self.gadget.parent_off() else "#90CAF9"


class HouseCard(BaseCard):
    def __init__(self, data=(), **kwargs):
        super(HouseCard, self).__init__(**kwargs)
        self.data = data
        Clock.schedule_once(self.load_widget)

    def load_widget(self, *args):
        for gadget in self.data:
            card = HouseListItem(gadget)
            self.ids.card.add_widget(card)


class RoomGadgetSwitchItem(MDBoxLayout):
    gadget = ObjectProperty()
    switch_thumb_color = ColorProperty("#2196F3")
    switch_track_color = ColorProperty("#90CAF9")

    def __init__(self, gadget, **kwargs):
        self.gadget = gadget
        super(RoomGadgetSwitchItem, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_switch_color, 1 / 20)

    def update_switch_color(self, dt):
        switch = self.ids.switch
        switch.thumb_color_active = "#B6B6B6" if self.gadget.parent_off() else "#2196F3"
        switch.track_color_active = "#DBDBDB" if self.gadget.parent_off() else "#90CAF9"



class RoomGadgetRegulateItem(MDBoxLayout):
    gadget = ObjectProperty()

    def __init__(self, gadget, **kwargs):
        self.gadget = gadget
        super(RoomGadgetRegulateItem, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_slider_color, 1 / 20)

    def update_slider_color(self, dt):
        slider = self.ids.slider
        parent_off = self.gadget.parent_off()
        if parent_off:
            slider.thumb_color_active = slider.thumb_color_inactive = "#B6B6B6"
            slider.color = "#DBDBDB"
        else:
            slider.thumb_color_active = slider.thumb_color_inactive = "#2196F3"
            slider.color = "#90CAF9"




class RoomListItem(CustomExpansionPanel):
    def __init__(self, room, **kwargs):
        super(RoomListItem, self).__init__(**kwargs)
        self.room = room
        Clock.schedule_once(self.load_widget)

    def load_widget(self, *args):
        room = self.room
        self.text = room.name.title()
        content_widget = Builder.load_string(content_widget_boxlayout)

        for gadget in room.gadgets.values():
            if gadget.control == "switch":
                list_item = RoomGadgetSwitchItem(gadget=gadget)
            else:  # gadget.control == "regulate"
                list_item = RoomGadgetRegulateItem(gadget=gadget)
            content_widget.add_widget(list_item)

        self.content = content_widget
        self.panel_state = "opened"


class RoomsCard(BaseCard):
    def __init__(self, data=None, **kwargs):
        super(RoomsCard, self).__init__(**kwargs)
        if data is None:
            data = []
        self.data = data
        Clock.schedule_once(self.load_widget)

    def load_widget(self, *args):
        for datum in self.data:
            self.ids.card.add_widget(RoomListItem(datum))


class SchedulesCard(BaseCard):
    def __init__(self, **kwargs):
        super(SchedulesCard, self).__init__(**kwargs)
        Clock.schedule_once(self.load_widget, 0)

    def load_widget(self, *args):
        pass


class HomePage(MDScreen):
    from homebot_config import config, Room, Gadget

    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)
        self.house_card = HouseCard(data=self.generate_house_card_items())
        self.rooms_card = RoomsCard(data=self.generate_rooms_card_items())
        self.schedules_card = SchedulesCard()
        Clock.schedule_once(self.load_widget)

    def generate_house_card_items(self):
        items = [self.config] + list(self.config.room_section_items.values())
        return tuple(items)

    def generate_rooms_card_items(self):
        items = []
        for gadget in self.config.room_section_items.values():
            if isinstance(gadget, self.Room):
                items.append(gadget)
        return items

    def load_widget(self, *args):
        self.ids.card.add_widget(self.house_card)
        self.prev_card = self.house_card
        self.ids["house"].selected = True

    def set_current(self, section):
        """
        changes the current card among the house, room and schedules card
        :param section: it's a string that can be "house", "room" or "schedules"
        :return: None
        """

        sections = ["house", "rooms", "schedules"]
        sections.remove(section)
        self.ids[section].selected = True

        for other_section in sections:
            self.ids[other_section].selected = False

        if section == "house":
            self.replace_card(self.house_card)
        elif section == "rooms":
            self.replace_card(self.rooms_card)
        elif section == "schedules":
            self.replace_card(self.schedules_card)

    def replace_card(self, card):
        self.ids.card.remove_widget(self.prev_card)
        self.ids.card.add_widget(card)
        self.prev_card = card
