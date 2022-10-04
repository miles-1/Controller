from etc import gamepad_decode_dict


def decodeEvent(event):
    decode = gamepad_decode_dict[event.code]
    # If Dpad
    if not isinstance(decode, str):
        name = "Dpad"
        if event.code[-1] == "X":
            val = ["X0", "R", "L"][event.state]
        elif event.code[-1] == "Y":
            val = ["Y0", "D", "U"][event.state]
    # Else non-Dpad
    else:
        name = decode
        val = event.state
    return {"name": name, "val": val, "time": event.timestamp}


def setEventData(digital_states, name, val, data_time):
    if name == "Dpad":
        if val == "X0":
            digital_states["LDpad"] = (0, data_time)
            digital_states["RDpad"] = (0, data_time)
        elif val == "Y0":
            digital_states["UDpad"] = (0, data_time)
            digital_states["DDpad"] = (0, data_time)
        else:
            digital_states[f"{val}Dpad"] = (1, data_time)
    else:
        digital_states[name] = (val, data_time)
