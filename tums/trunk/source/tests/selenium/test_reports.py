import sys
sys.path.append('C:\\tests\\lib')

from selenium import selenium
import unittest, time, re

class test_reports(unittest.TestCase):

    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://172.31.0.222:9682/")
        self.selenium.start()

    def test_test_reports(self):
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

        # perform rendering tests
        sel.click("link=Reports")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Disk usage
        sel.click("link=Disk Usage")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Test log viewer
        sel.click("link=Log Viewer")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.select("selectLog-log", "label=Syslog")
        sel.click("selectLog-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=3")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=1")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.type("filterLog-filter", "Shorewall")
        sel.click("filterLog-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.type("filterLog-filter", "--Shorewall")
        sel.click("filterLog-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
    
        # Mail logs
        sel.click("link=9")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Mail Logs")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.type("searchForm-to", "root@bulwer.thusa.net")
        sel.click("searchForm-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Mail Logs")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Next 20")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Mail Statistics")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("selectDate-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Mail Queue")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Network Utilisation")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=System Statistics")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("//div[@id='pageContent']/table/tbody/tr[2]/td/div/div[2]/table/tbody/tr/td[2]/a/img")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        sel.click("link=Updates")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.click("//a[@id='tabpanelWindows']/strong")
        sel.click("//a[@id='tabpanelLinux']/strong")
        sel.click("//a[@id='tabpanelStats']/strong")

        # Web usage
        sel.click("link=Web Usage")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
