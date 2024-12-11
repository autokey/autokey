import threading
from autokey.iomediator.interface_wayland import IoInterfaceWayland

class IoMediatorWayland(threading.Thread):
    """
    Mediator for handling IO events under Wayland.
    """

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.interface = IoInterfaceWayland(service)
        self.running = False

    def run(self):
        """
        Start the mediator loop.
        """
        self.running = True
        self.interface.run()

    def shutdown(self):
        """
        Shutdown the mediator.
        """
        self.running = False
        self.interface.shutdown() 