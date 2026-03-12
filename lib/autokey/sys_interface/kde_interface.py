class FakeWindowInfo:
    def __init__(self, title, cls):
        self.wm_title = title
        self.wm_class = cls
    
    # This allows the object to act like a list [0]
    def __getitem__(self, index):
        if index == 0: return self.wm_title
        if index == 1: return self.wm_class
        return "Unknown"

class KDEWaylandInterface:
    def get_window_info(self, *args, **kwargs):
        return FakeWindowInfo("Unknown", "UnknownClass")
