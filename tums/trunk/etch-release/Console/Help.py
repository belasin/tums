import Console

class HelpHooker(Console.ActionHooker): #ReWrite
    def __repr__(self):
        return """Avaliable Commands:
    config  - Configure settings
    show    - Show settings and statistics
    service - Allows the user to start and stop services

Individual commands show parameters and sub commands
"""

