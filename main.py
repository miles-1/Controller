from inputs import get_gamepad
from time import time
from user_params import max_history, show_graphs, scroll_scale, move_scale, sim_commands
from gamepad import decodeEvent, setEventData
from graph import graphEvents
from etc import gamepad_events, sim_event_type, Operator
import sys
import ctypes

ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)

def processTimestamp(time_series, digital_states, max_history=max_history):
    for event_type, (val, time) in digital_states.items():
        if len(time_series[event_type]) >= max_history:
            time_series[event_type].pop(0)
        time_series[event_type].append([time, val])
    for event_type, history in time_series.items():
        if (("L" in event_type and "Stick" in event_type and "Click" not in event_type) or "Trigger" in event_type) \
           and history and event_type not in digital_states:
           digital_states[event_type] = tuple(history[-1][i] for i in (1, 0))


def main():
    try:
        start_time = time()
        operator = Operator(sim_commands, sim_event_type, (scroll_scale, move_scale))
        time_series = {common_name: [] for common_name in gamepad_events} # timeseries value
        while True:
            events = get_gamepad()
            digital_states = {} # event_type: (val, time)
            for event in events:
                if event.ev_type in ("Key", "Absolute"):
                    name, val, event_time = [decodeEvent(event)[key] for key in ("name", "val", "time")]
                    data_time = event_time - start_time
                    setEventData(digital_states, name, val, data_time)
            processTimestamp(time_series, digital_states)
            operator.runSims(time_series, digital_states)

    except KeyboardInterrupt:
        if show_graphs:
            graphEvents(time_series, time()-start_time)
        sys.exit(1)

if __name__ == "__main__":
    main()