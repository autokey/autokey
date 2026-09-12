X_RECORD_INTERFACE = "XRecord"
WAYLAND_INTERFACE = "Wayland"
ATSPI_INTERFACE = "AtSpi"

def get_display_server():
    import os
    if 'WAYLAND_DISPLAY' in os.environ:
        return 'wayland'
    elif 'DISPLAY' in os.environ:
        return 'x11'
    return 'unknown'

def get_interface_type():
    display = get_display_server()
    if display == 'wayland':
        try:
            from autokey.iomediator.wayland_backend import WaylandInterface
            WaylandInterface()
            return WAYLAND_INTERFACE
        except ImportError:
            return ATSPI_INTERFACE
    return X_RECORD_INTERFACE