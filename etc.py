import pyautogui
from winsound import PlaySound, SND_FILENAME
from sys import argv
from os.path import dirname, join

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

ANALOG = -2
DIGITAL = -1
INSTANT = 0
HOLD = 1
CONTINUOUS = 2

sim_event_type = {
    "Toggle": INSTANT,
    "LClick": INSTANT,
    "RClick": INSTANT,
    "Up": INSTANT,
    "Down": INSTANT,
    "Left": INSTANT,
    "Right": INSTANT,
    "Win": INSTANT,
    "Enter": INSTANT,
    "Minimize": INSTANT,
    "XScroll": CONTINUOUS,
    "YScroll": CONTINUOUS,
    "XMove": CONTINUOUS,
    "YMove": CONTINUOUS
}

gamepad_decode_dict = {
    # code_name: common_name
    "BTN_SOUTH": "A",
    "BTN_EAST": "B",
    "BTN_WEST": "X",
    "BTN_NORTH": "Y",
    "BTN_SELECT": "Menu",
    "BTN_START": "Start",
    "BTN_THUMBL": "LStickClick",
    "BTN_THUMBR": "RStickClick",
    "BTN_TL": "LBumper",
    "BTN_TR": "RBumper",
    "ABS_HAT0X": ["Dpad", "RDpad", "LDpad"],
    "ABS_HAT0Y": ["Dpad", "DDpad", "UDpad"],
    "ABS_Z": "LTrigger",
    "ABS_RZ": "RTrigger",
    "ABS_X": "LXStick",
    "ABS_Y": "LYStick",
    "ABS_RX": "RXStick",
    "ABS_RY": "RYStick"
}

gamepad_events = \
    ("RDpad", "LDpad", "DDpad", "UDpad") + \
    tuple(event_info for event_info 
                     in gamepad_decode_dict.values() 
                     if isinstance(event_info, str))

gamepad_event_type = \
    {event:(DIGITAL if ("Stick" in event and "Click" not in event) 
                        or "Trigger" in event
                    else ANALOG)
        for event in gamepad_events}


class hyperkey(dict):
    def __init__(self, keyset):
        self.keyset_dict = {item:num for num, item in enumerate(keyset)}
        super().__init__()
    
    def __setitem__(self, keys, value):
        return super().__setitem__(self._getHyperkey(keys), value)
    
    def __getitem__(self, keys):
        reqsd_hyperkey = set(self._getHyperkey(keys))
        values = []
        for hyperkey in self:
            if set(hyperkey).issubset(reqsd_hyperkey):
                reqsd_hyperkey.difference_update(set(hyperkey))
                values.append(super().__getitem__(hyperkey))
        return values
    
    def _getHyperkey(self, keys):
        return tuple(sorted(self.keyset_dict[key] for key in keys if key in self.keyset_dict))


class Operator:
    def __init__(self, sim_commands, sim_info_dict, scale):
        # setup
        self.translation_active = True
        self.current_gamepad_states = {}
        self.recently_ran_dict = {}
        self.cont_sims_dict = {}
        self.scroll_scale = scale[0]
        self.move_scale = scale[1]
        # get temp lsts from sim_commands
        temp_cmd_lst, temp_button_set = [], set()
        temp_inactive_cmd_lst, temp_inactive_button_set = [], set()
        for sim in sim_commands:
            gamepad_event, sim_event = sim.replace(" ", "").split("->")
            buttons = gamepad_event.split("+")
            temp_button_set.update(set(buttons))
            temp_cmd_lst.append([buttons, sim_event])
            # make dicts
            if sim_info_dict[sim_event] == INSTANT:
                self.recently_ran_dict[sim_event] = False
            elif sim_info_dict[sim_event] == CONTINUOUS:
                self.cont_sims_dict[sim_event] = buttons[0] # assume only one button
            # make inactive dict
            if sim_event == "Toggle":
                temp_inactive_button_set.update(set(buttons))
                temp_inactive_cmd_lst.append([buttons, sim_event])
        # make command dictionaries
        self.cmd_dict = hyperkey(temp_button_set)
        self.inactive_cmd_dict = hyperkey(temp_inactive_button_set)
        for buttons, sim_event in temp_cmd_lst:
            self.cmd_dict[buttons] = sim_event
        for buttons, sim_event in temp_inactive_cmd_lst:
            self.inactive_cmd_dict[buttons] = sim_event
        
    def runSims(self, time_series, digital_states):
        sim_events = self._getSimsFromSeries(time_series, digital_states)
        recently_ran = self._getAndResetRecentlyRanDict()
        print(sim_events)
        for sim_event in sim_events:
            if sim_event == "Toggle" and not recently_ran[sim_event]:
                self.recently_ran_dict[sim_event] = True
                self.translation_active = not self.translation_active
                globals()[sim_event](self.translation_active)
            elif sim_event in recently_ran \
               and not recently_ran[sim_event]:
                self.recently_ran_dict[sim_event] = True
                globals()[sim_event]()
            elif sim_event in self.cont_sims_dict:
                gamepad_event = self.cont_sims_dict[sim_event]
                gamepad_state = self.current_gamepad_states[gamepad_event]
                if "Scroll" in sim_event:
                    globals()[sim_event](gamepad_state, self.scroll_scale)
                else:
                    globals()[sim_event](gamepad_state, self.move_scale) # TODO fix recently ran by fixing release button data loss
            

    def _getSimsFromSeries(self, time_series, digital_states):
        self.current_gamepad_states.clear()
        for gamepad_event, history in time_series.items():
            if history and not (("Stick" in gamepad_event and "Click" not in gamepad_event) 
                        or "Trigger" in gamepad_event):
                state = history[-1][1]
                if state:
                    self.current_gamepad_states[gamepad_event] = state
        for gamepad_event, (state, _) in digital_states.items():
            if gamepad_event in self.cont_sims_dict.values() and abs(state) > 2000:
                self.current_gamepad_states[gamepad_event] = state
        if self.translation_active:
            return self.cmd_dict[self.current_gamepad_states]
        else:
            return self.inactive_cmd_dict[self.current_gamepad_states]
    
    def _getAndResetRecentlyRanDict(self):
        recently_ran_dict_copy = self.recently_ran_dict.copy()
        self.recently_ran_dict = {key: False for key in self.recently_ran_dict}
        return recently_ran_dict_copy

#### functions


folder_name = dirname(argv[0])
sound_on_path = join(folder_name, "on.wav")
sound_off_path = join(folder_name, "off.wav")

def Toggle(translation_active):
    if translation_active:
        PlaySound(sound_on_path, SND_FILENAME)
    else:
        PlaySound(sound_off_path, SND_FILENAME)

def LClick():
    pyautogui.click() 

def DoubleLClick():
    pyautogui.doubleClick()

def RClick():
    pyautogui.click(button='right')

def XMove(amnt, scale):
    pyautogui.moveRel(int(amnt*scale), 0, _pause=False)

def YMove(amnt, scale):
    pyautogui.moveRel(0, -int(amnt*scale), _pause=False)

def XScroll(amnt, scale):
    pyautogui.scroll(int(amnt*scale), _pause=False)

def YScroll(amnt, scale):
    pyautogui.keyDown('shift')
    pyautogui.scroll(int(amnt*scale), _pause=False)
    pyautogui.keyUp('shift')

def Tab():
    pyautogui.press('tab')

def RevTab():
    pyautogui.keyDown('shift')
    pyautogui.press('tab')
    pyautogui.keyUp('shift')

def Win():
    pyautogui.press('win')

def Up():
    pyautogui.press('up')

def Down():
    pyautogui.press('down')

def Left():
    pyautogui.press('left')

def Right():
    pyautogui.press('right')

def Minimize():
    pyautogui.keyDown('winleft')
    pyautogui.press('d')
    pyautogui.keyUp('winleft')

def Enter():
    pyautogui.press('enter')
