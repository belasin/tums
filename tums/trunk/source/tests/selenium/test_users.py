import sys
sys.path.append('C:\\tests\\lib')

from selenium import selenium
import unittest, time, re

class test_dashboard(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://172.31.0.222:9682/")
        self.selenium.start()
    
    def test_test_users(self):
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

        # Open users tree. 
        sel.click("link=Users")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        #sel.click("//img[contains(@src,'http://172.31.0.222:9682/images/dhtmlgoodies_minus.gif')]")

        # Add a domain
        sel.click("link=Add Domain")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.type("addForm-domainName", "test.net")
        sel.click("addForm-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Create a user in this domain
        sel.open('/auth/Users/Add/test.net/')
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.type("addForm-userSettings-uid", "test")
        sel.type("addForm-userSettings-givenName", "test")
        sel.type("addForm-userSettings-userPassword", "test")
        sel.type("addForm-userSettings-userPassword-confirm", "test")
        sel.click("//a[@id='tabaddForm-userPermissions']/strong")
        sel.click("addForm-userPermissions-employeeType")
        sel.click("addForm-userPermissions-tumsUser-1")
        sel.click("//a[@id='tabaddForm-mailSettings']/strong")
        sel.click("//a[@id='tabaddForm-userAccess']/strong")
        sel.click("addForm-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))

        # Modify the user (we should be redirected to the edit page)
        sel.type("editForm-userSettings-userPassword", "test123")
        sel.type("editForm-userSettings-userPassword-confirm", "test123")
        sel.type("editForm-userSettings-sn", "new")
        sel.type("editForm-userSettings-givenName", "new")
        sel.type("editForm-userSettings-uid", "testrenamed")
        sel.type("editForm-userSettings-userPassword", "test123")
        sel.click("editForm-action-submit")

        # Delete the user
        sel.wait_for_page_to_load("30000")
        sel.click("link=Delete User")
        self.failUnless(re.search(r"^Are you sure you want to delete this user[\s\S]$", sel.get_confirmation()))

        # Delete the domain
        sel.click("link=Delete Domain")
        self.failUnless(re.search(r"^Are you sure you want to delete this domain[\s\S]$", sel.get_confirmation()))

        # Add a user to the default tree
        sel.open('/auth/Users/Add/bulwer.thusa.net/')
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.click("//a[@id='tabaddForm-userSettings']/strong")
        sel.type("addForm-userSettings-uid", "test")
        sel.type("addForm-userSettings-givenName", "test123")
        sel.type("addForm-userSettings-sn", "test")
        sel.type("addForm-userSettings-userPassword", "test123")
        sel.type("addForm-userSettings-userPassword-confirm", "test123")
        sel.click("addForm-action-submit")

        # Edit user
        sel.wait_for_page_to_load("30000")
        sel.click("//a[@id='tabeditForm-userPermissions']/strong")
        sel.click("editForm-userPermissions-employeeType")
        sel.click("editForm-userPermissions-accountStatus")
        sel.click("editForm-userPermissions-tumsAdmin")
        sel.click("editForm-userPermissions-tumsUser-0")
        sel.click("editForm-userPermissions-tumsReports")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.click("//a[@id='tabeditForm-mailSettings']/strong")
        sel.type("editForm-mailSettings-mailForwardingAddress0", "nobody@bulwer.thusa.net")
        sel.type("editForm-mailSettings-mailAlternateAddress0", "foo@bulwer.thusa.net")
        sel.click("//a[@onclick='addAlias();']")
        sel.type("editForm-mailSettings-mailAlternateAddress2", "bar@bulwer.thusa.net")
        sel.click("editForm-mailSettings-vacen")
        sel.type("editForm-mailSettings-vacation", "vacation")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        sel.type("editForm-mailSettings-mailAlternateAddress1", "")
        sel.type("editForm-mailSettings-mailAlternateAddress0", "")
        sel.type("editForm-mailSettings-mailForwardingAddress0", "")
        sel.click("editForm-mailSettings-vacen")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        sel.type("editForm-mailSettings-vacation", "new vacation (disabled)")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        sel.click("//a[@id='tabeditForm-userPermissions']/strong")
        sel.click("editForm-userPermissions-accountStatus")
        sel.click("editForm-userPermissions-employeeType")
        sel.click("editForm-userPermissions-tumsAdmin")
        sel.click("editForm-userPermissions-tumsReports")
        sel.click("editForm-userPermissions-tumsUser-0")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        sel.click("//a[@id='tabeditForm-userSettings']/strong")

        # Test group systems
        sel.click("link=Edit Memberships")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.click("editForm-DomainUsers")
        sel.click("editForm-DomainGuests")
        sel.click("editForm-DomainUsers")
        sel.click("editForm-DomainGuests")
        sel.click("editForm-BackupOperators")
        sel.click("editForm-PrintOperators")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.click("link=Edit Memberships")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.click("link=Create Group")
        sel.wait_for_page_to_load("30000")
        self.failIf(sel.is_text_present("An error has occurred"))
        sel.type("editForm-groupName", "foo")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        sel.click("node_4")
        sel.wait_for_page_to_load("30000")

        sel.click("//div[@id='rightBlock']/table/tbody/tr[10]/td[2]/a")
        sel.wait_for_page_to_load("30000")
        sel.click("editForm-dGVzdA__")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Create Group")
        sel.wait_for_page_to_load("30000")
        sel.type("editForm-groupName", "foo")
        sel.click("editForm-action-submit")
        sel.wait_for_page_to_load("30000")
        sel.click("node_8")
        sel.wait_for_page_to_load("30000")

        # Finaly delete the user
        sel.click("link=Delete User")
        self.failUnless(re.search(r"^Are you sure you want to delete this user[\s\S]$", sel.get_confirmation()))
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()

