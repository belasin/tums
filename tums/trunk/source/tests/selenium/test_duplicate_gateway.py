import sys
sys.path.append('C:\\tests\\lib')

from selenium import selenium
import unittest, time, re

class test_duplicate_routes(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://172.31.0.222:9682/")
        self.selenium.start()

    def test_test_duplicate_routes(self):
        sel = self.selenium
        sel.open("/auth/")
        sel.wait_for_page_to_load("30000")
        sel.type("username", "administrator")
        sel.type("password", "admin123")
        sel.click("//input[@value='Login']")
        sel.wait_for_page_to_load("30000")

        # Explicitly set the URL. Page redirection from login confuses Selenium greatly
        sel.open("/auth/Routing/")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Set some default route (hopefully overwriting any others)
        sel.type("statroutes-dest", "0.0.0.0/0")
        sel.type("statroutes-gate", "172.31.0.1")
        sel.select("statroutes-device", "label=eth0")
        sel.click("statroutes-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Open our eth1 and set the gateway
        sel.open("/auth/Network/Edit/eth1/")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.type("modInterface-gateway", "172.31.0.2")
        sel.click("modInterface-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Open our eth0 and set the gateway
        sel.open("/auth/Network/Edit/eth0/")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.type("modInterface-gateway", "172.31.0.1")
        sel.click("modInterface-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
