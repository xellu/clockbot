from .templates.ConfigTemplate import ConfigTemplate
from .config import ConfigManager

from colorama import Fore

Config = ConfigManager("config.json", template=ConfigTemplate)
Banner = f"""{Fore.BLUE}            _ _   _   
    _____ _| | |_| |_ 
   |     | . | . | . |
   |_|_|_|___|___|___|
 A Modular Discord Bot Base
 {Fore.BLACK}███{Fore.RED}███{Fore.GREEN}███{Fore.YELLOW}███{Fore.BLUE}███{Fore.MAGENTA}███{Fore.CYAN}███{Fore.WHITE}███
 {Fore.LIGHTBLACK_EX}███{Fore.LIGHTRED_EX}███{Fore.LIGHTGREEN_EX}███{Fore.LIGHTYELLOW_EX}███{Fore.LIGHTBLUE_EX}███{Fore.LIGHTMAGENTA_EX}███{Fore.LIGHTCYAN_EX}███{Fore.LIGHTWHITE_EX}███{Fore.RESET}"""