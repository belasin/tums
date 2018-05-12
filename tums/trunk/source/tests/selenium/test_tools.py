import sys
sys.path.append('C:\\tests\\lib')

from selenium import selenium
import unittest, time, re

class test_tools(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://172.31.0.222:9682/")
        self.selenium.start()

    def test_test_tools(self):
        sel = self.selenium
        sel.open("/auth/")
        sel.wait_for_page_to_load("30000")
        sel.type("username", "administrator")
        sel.type("password", "admin123")
        sel.click("//input[@value='Login']")
        sel.wait_for_page_to_load("30000")

        # Explicitly set the URL. Page redirection from login confuses Selenium greatly
        sel.open("/auth/Tools/")
        sel.wait_for_page_to_load("30000")

        # Perform rendering tests
        sel.click("//div[@id='sideContTools']/div[1]/div[1]")
        sel.click("link=VPN")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=SSH")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("//div[@id='sideContTools']/div[2]/div[1]")
        sel.click("link=Firewall")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Interfaces")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Broadband")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Routing")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=DNS")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=DHCP")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("//div[@id='sideContTools']/div[3]/div[1]")
        sel.click("link=Domain")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Shares")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("//div[@id='sideContTools']/div[4]/div[1]")
        sel.click("link=Backups")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=File Browser")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Profiles")
        sel.click("//div[@id='sideContTools']/div[6]/div[1]")
        sel.click("link=Manage")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Web Proxy")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Diagnostics
        sel.click("//div[@id='sideContTools']/div[9]/div[1]")
        sel.click("link=Mail")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Network")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Mail server
        sel.click("//div[@id='sideContTools']/div[10]/div[1]")
        sel.click("link=Mail Server")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # HA
        sel.click("link=High Availability")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
