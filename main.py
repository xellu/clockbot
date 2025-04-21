from colorama import Fore

print(f"""{Fore.BLUE}            
            _ _   _   
    _____ _| | |_| |_ 
   |     | . | . | . |
   |_|_|_|___|___|___|
 A Modular Discord Bot Base{Fore.RESET}""")

import core
import cogs

from core.bot import run

run()