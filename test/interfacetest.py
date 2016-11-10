import unittest, time

from lib import interface, iomediator

class XLibInterfaceTest(unittest.TestCase):
    
    def setUp(self):
        self.service = MockService()
        self.mediator = iomediator.IoMediator(self.service, iomediator.XLIB_INTERFACE)
        self.mediator.start()
        self.interface = self.mediator.interface
        
    def testget_event_count(self):
        self.assertEqual(self.interface.get_event_count('a'), 1)
        self.assertEqual(self.interface.get_event_count('b'), 1)
        self.assertEqual(self.interface.get_event_count('c'), 1)
        self.assertEqual(self.interface.get_event_count('d'), 1)
        self.assertEqual(self.interface.get_event_count('e'), 1)
        self.assertEqual(self.interface.get_event_count('f'), 1)
        self.assertEqual(self.interface.get_event_count('g'), 1)
        self.assertEqual(self.interface.get_event_count('h'), 1)
        self.assertEqual(self.interface.get_event_count('i'), 1)
        self.assertEqual(self.interface.get_event_count('j'), 1)
        self.assertEqual(self.interface.get_event_count('k'), 1)
        self.assertEqual(self.interface.get_event_count('l'), 1)
        self.assertEqual(self.interface.get_event_count('m'), 1)
        self.assertEqual(self.interface.get_event_count('n'), 1)
        self.assertEqual(self.interface.get_event_count('o'), 1)
        self.assertEqual(self.interface.get_event_count('p'), 1)
        self.assertEqual(self.interface.get_event_count('q'), 1)
        self.assertEqual(self.interface.get_event_count('r'), 1)
        self.assertEqual(self.interface.get_event_count('s'), 1)
        self.assertEqual(self.interface.get_event_count('t'), 1)
        self.assertEqual(self.interface.get_event_count('u'), 1)
        self.assertEqual(self.interface.get_event_count('v'), 1)
        self.assertEqual(self.interface.get_event_count('w'), 1)
        self.assertEqual(self.interface.get_event_count('x'), 1)
        self.assertEqual(self.interface.get_event_count('y'), 1)
        self.assertEqual(self.interface.get_event_count('z'), 1)
        
        self.assertEqual(self.interface.get_event_count('A'), 2)
        self.assertEqual(self.interface.get_event_count('Z'), 2)
        
        self.assertEqual(self.interface.get_event_count('1'), 1)
        
        self.assertEqual(self.interface.get_event_count('~'), 2)
        self.assertEqual(self.interface.get_event_count('-'), 1)
        self.assertEqual(self.interface.get_event_count('_'), 2)
        self.assertEqual(self.interface.get_event_count('/'), 1)
        self.assertEqual(self.interface.get_event_count('?'), 2)
        self.assertEqual(self.interface.get_event_count('\\'), 1)
        self.assertEqual(self.interface.get_event_count('|'), 2)
        
        self.assertEqual(self.interface.get_event_count('\n'), 1)
        
        self.assertEqual(self.interface.get_event_count(' '), 1)
        
        self.assertEqual(self.interface.get_event_count("/opt/Dialect/PE/Portals"), )
        
    def tearDown(self):
        self.mediator.pause()
        
        
class MockService:
    
    def handle_keypress(self, key):
        self.key = key

    
    