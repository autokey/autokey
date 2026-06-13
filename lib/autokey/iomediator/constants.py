X_RECORD_INTERFACE = "XRecord"
WAYLAND_INTERFACE = "Wayland"

def get_display_server():
    import os
    if 'WAYLAND_DISPLAY' in os.environ:
        return 'wayland'
    elif 'DISPLAY' in os.environ:
        return 'x11'
    return 'unknown'

def get_interface_type():
    display = get_display_server()
    if display == 'wayland' and HAS_WAYLAND:
        return WAYLAND_INTERFACE
    return X_RECORD_INTERFACE
