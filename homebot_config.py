"""
HomeBotDDL is a data definition language for defining the structure of controlled building
defining the rooms and gadgets in the building.
it is represented with string of characters with certain the following rules:

    Preceding Keys:
        $N() - Name of an object
        $C() - control, which can be followed by switch or regulate
        $G() - gadgets
    Gadget:
        {$N(name)$C(control)}
    Room:
        [$N(name)$G(Gadget Gadget ...)]
    HomeBotDDL:
        Rooms
        Gadgets - gadget controlled not in a room

"""


def not_found(index, error_msg):
    if index == -1:
        raise HomeBotDDLSyntaxError(error_msg)


class HomeBotDDLSyntaxError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class Gadget:
    def __init__(self, name="", control="switch", parent=None):
        """
            it represents gadgets/appliances in the building which can be controlled by a switch (on/off)
        or regulated output which be represented as percentage output
        :param name: name of the gadget
        :param control: type of control which can be "switch" or "regulate"
        :param parent: HomeBotConfig or Room object
        """
        assert control in ["switch", "regulate"], "Gadget: control should be 'switch' or 'regulate'"
        self.name = name
        self.control = control
        if self.control == "switch":
            self.state = "on"
        elif self.control == "regulate":
            self.state = 100
        # state is "on" or "off" if control is "switch" else if "regulate" state is a number in [0, 100]
        self.parent = parent

    def parent_off(self):
        if self.parent is None:
            return False
        return self.parent.state == "off" or self.parent.parent_off()

    @property
    def path(self):
        if isinstance(self.parent, Room):
            return f"{self.parent.path}/{self.name}"
        elif isinstance(self.parent, HomeBotConfig):
            return f"{self.parent.name}/{self.name}"
        raise Exception("Gadget: path property not accessible since parent is None")

    @property
    def ddl(self):
        return f"{{ $N({self.name}) $C({self.control}) }}"

    @staticmethod
    def parse_ddl(ddl_string: str):
        """
        creates a gadget object by parsing ddl_string
        :param ddl_string: HomeBotDDL representation for gadget objects
        :return: Gadget
        """

        start_index = ddl_string.find("$N(")
        not_found(start_index, "gadget object name not declared")

        stop_index = ddl_string.find(')', start_index)
        not_found(stop_index, "$N( name notation not closed with ')'")

        name = ddl_string[start_index + 3: stop_index].strip()

        start_index = ddl_string.find("$C(", stop_index + 1)
        not_found(start_index, "gadget object control not declared")

        stop_index = ddl_string.find(')', start_index)
        not_found(stop_index, "$C( name notation not closed with ')'")

        control = ddl_string[start_index + 3: stop_index].strip()

        return Gadget(name, control)


class Room(Gadget):
    def __init__(self, gadgets=None, **kwargs):
        """
            it represents a room in a building with a collection of Gadget objects
        :param gadgets: collection of the Gadgets in the room which is a dictionary with name of gadgets as keys and
                        gadget object as values
        """
        super(Room, self).__init__(**kwargs)

        if gadgets is None:
            self.gadgets = {}
        else:
            self.gadgets = gadgets
            for gadget in self.gadgets.values():
                gadget.parent = self

    def __getitem__(self, path: str):
        path = path.strip("/").split("/", 1)
        if path[0] == self.name:
            if len(path) == 1:
                return self
            else:
                item = self.gadgets.get(path[1])
                if item is None:
                    raise PathNotFoundError()
                return item
        else:
            raise PathNotFoundError()

    @property
    def path(self):
        if self.parent is None:
            raise Exception("Room: path property not accessible since parent is None")
        return f"{self.parent.name}/{self.name}"

    @property
    def paths_all(self):
        """
        :return: the path of all the gadgets in the room
        """
        paths = [self.path]
        paths.extend((gadget.path for gadget in self.gadgets.values()))
        return tuple(paths)

    @property
    def ddl(self):
        ddl = f"[ $N({self.name}) $G("
        for gadget in self.gadgets.values():
            ddl += " " + gadget.ddl
        ddl += " ) ]"
        return ddl

    @staticmethod
    def parse_ddl(ddl_string: str):
        """
        creates a room object by parsing ddl_string
        :param ddl_string: HomeBotDDL representation for room objects
        :return: Room
        """

        start_index = ddl_string.find("$N(")
        not_found(start_index, "room object name not declared")

        stop_index = ddl_string.find(')', start_index)
        not_found(stop_index, "$N( name notation not closed with ')'")

        name = ddl_string[start_index + 3: stop_index].strip()

        start_index = ddl_string.find("$G(", stop_index + 1)
        not_found(start_index, "room gadgets not declared")
        stop_index = start_index + 3

        gadgets = {}
        while True:
            if ddl_string.find('{', stop_index) == -1:
                break

            start_index = ddl_string.find('{', stop_index)
            stop_index = ddl_string.find('}', start_index)
            not_found(stop_index, "declaration of gadget not closed with '}'")
            gadget = Gadget.parse_ddl(ddl_string[start_index:stop_index + 1])
            gadgets[gadget.name] = gadget

        stop_index = ddl_string.find(')', start_index)
        not_found(stop_index, "$G( gadgets notation not closed with ')'")

        return Room(name=name, gadgets=gadgets)


class HomeBotConfig(Gadget):
    def __init__(self, items=None, **kwargs):
        super(HomeBotConfig, self).__init__(**kwargs)
        if items is None:
            items = {}
        self.room_section_items = items

        for items in self.room_section_items.values():
            items.parent = self

    def __getitem__(self, path: str):
        path = path.strip("/").split("/")
        if path[0] == self.name:
            if len(path) == 1:
                return self
            else:
                item = self.room_section_items.get(path[1])
                if item is None:
                    raise PathNotFoundError()
                elif isinstance(item, Gadget) and len(path) == 2:
                    return item
                elif isinstance(item, Room):
                    # room __getitem__
                    return item["/".join(path[1:])]
        raise PathNotFoundError()

    @property
    def paths_all(self):
        paths = [self.name]
        for item in self.room_section_items.values():
            if isinstance(item, Room):
                paths.extend(item.paths_all)
            elif isinstance(item, Gadget):
                paths.extend([item.path])
        return tuple(paths)

    @property
    def ddl(self):
        ddl = f"$N({self.name})"

        for item in self.room_section_items.values():
            ddl += "\n" + item.ddl

        return ddl

    @staticmethod
    def parse_ddl(ddl_string: str):
        def room_next(string: str):
            room = string.find('[')
            return room >= 0 and string[:room].strip() == ""

        def gadget_next(string: str):
            gadget = string.find('{')
            return gadget >= 0 and string[:gadget].strip() == ""

        def has_name():
            index = ddl_string.find("$N(")
            return ddl_string[:index].strip() == ""

        homebot_config = HomeBotConfig()
        if has_name():
            start_index = ddl_string.find("$N(")
            stop_index = ddl_string.find(")")
            not_found(stop_index, "$N( name of building not closed with ')'")
            homebot_config.name = ddl_string[start_index + 3: stop_index].strip()
        else:
            stop_index = 0
            homebot_config.name = "house"

        room_section_items = {}
        while True:
            if room_next(ddl_string[stop_index + 1:]):
                start_index = ddl_string.find('[', stop_index + 1)
                stop_index = ddl_string.find(']', start_index)
                room = Room.parse_ddl(ddl_string[start_index: stop_index])
                room_section_items[room.name] = room
            elif gadget_next(ddl_string[stop_index + 1:]):
                start_index = ddl_string.find('{', stop_index + 1)
                stop_index = ddl_string.find('}', start_index)
                gadget = Gadget.parse_ddl(ddl_string[start_index: stop_index])
                room_section_items[gadget.name] = gadget
            else:
                break

        for item in room_section_items.values():
            item.parent = homebot_config

        homebot_config.room_section_items = room_section_items

        return homebot_config


ddl = """
[
    $N(parlor)
    $G(
        {$N(light1) $C(switch)}
        {$N(light2) $C(switch)}
        {$N(fan1) $C(regulate)}
        {$N(fan2) $C(regulate)}
    )
]
[
    $N(girls room)
    $G(
        {$N(light) $C(switch)}
        {$N(fan) $C(regulate)}
    )
]
[
    $N(boys room)
    $G(
        {$N(light) $C(switch)}
        {$N(fan) $C(regulate)}
    )
]
[
    $N(parents room)
    $G(
        {$N(light) $C(switch)}
        {$N(fan) $C(regulate)}
    )
]
[
    $N(guest room)
    $G(
        {$N(light) $C(switch)}
        {$N(alarm) $C(switch)}
        {$N(AC) $C(regulate)}
    )
]
{$N(kitchen light) $C(switch)}
{$N(toilet light) $C(switch)}
{$N(store light) $C(switch)}
{$N(outside light) $C(switch)}
{$N(pumping machine) $C(switch)}
"""
config = HomeBotConfig.parse_ddl(ddl)


