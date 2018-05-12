
class Text:
    def __init__(self, lang):
        self.templates = "lang/%s/templates/" % lang
        try:
            self.lang = __import__("lang."+lang, globals(), locals(), ['lang'])
        except:
            print "Unable to find selected language module - eek"

    def __getattr__(self, text):
        try:
            return getattr(self.lang, text)
        except:
            print "Unable to find text lable", text
            return text
