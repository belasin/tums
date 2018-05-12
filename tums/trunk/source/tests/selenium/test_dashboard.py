import sys
sys.path.append('C:\\tests\\lib')

from selenium import selenium
import unittest, time, re

class test_dashboard(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://172.31.0.222:9682/")
        self.selenium.start()
    
    def test_test_dashboard(self):
        sel = self.selenium
        sel.open("/auth/")
        sel.wait_for_page_to_load("30000")
        sel.type("username", "administrator")
        sel.type("password", "admin123")
        sel.click("//input[@value='Login']")
        sel.wait_for_page_to_load("30000")

        # Explicitly set the URL. Page redirection from login confuses Selenium greatly
        sel.open("/auth/Status/")
        sel.wait_for_page_to_load("30000")
        
        requiresElements = [
            "profileSwitchTable", 
            "uptimeBlock",
            "processTable",
            "sysRAID"
        ]
        
        for element in requiresElements:
            print element,
            self.failUnless(sel.is_element_present(element))
            print "  [OK]"

        self.failIf(sel.is_text_present("An error has occurred"))

    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
