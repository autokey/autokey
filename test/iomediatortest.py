import unittest

from lib.iomediator import *

class IoMediatorTest(unittest.TestCase):
    
    def testKeySplitRe(self):
        result = KEY_SPLIT_RE.split("<ctrl>+y")
        self.assertEqual(result, ["", "<ctrl>+", "y"])
        
        result = KEY_SPLIT_RE.split("asdf <ctrl>+y asdf ")
        self.assertEqual(result, ["asdf ", "<ctrl>+", "y asdf "])
        
        result = KEY_SPLIT_RE.split("<table><ctrl>+y</table>")
        self.assertEqual(result, ["", "<table>", "", "<ctrl>+", "y", "</table>", ""])
        
        result = KEY_SPLIT_RE.split("<!<alt_gr>+8CDATA<alt_gr>+8")
        self.assertEqual(result, ["<!", "<alt_gr>+", "8CDATA", "<alt_gr>+", "8"])
        
        result = KEY_SPLIT_RE.split("<ctrl>y")
        self.assertEqual(result, ["", "<ctrl>", "y"])
        
        result = KEY_SPLIT_RE.split("Test<tab>More text")
        self.assertEqual(result, ["Test", "<tab>", "More text"])        