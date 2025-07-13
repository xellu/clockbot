from core import WORD_BLACKLIST

import string
import re

class WordBlacklistManager:
    def __init__(self):
        """
        Initialize the WordBlacklistManager.
        Loads the blacklist from a file.
        """
        self.leet = {
            "1": "i",
            "2": "z",
            "3": "e",
            "4": "a",
            "5": "s",
            "6": "g",
            "7": "t",
            "0": "o",
        }
    
    def match(self, text: str) -> str | None:
        """
        Check if the text contains any blacklisted words.
        Returns the first matched word or None if no match is found.
        """
        text = self.de_unicode(text)
        
        leet = self.de_leet(text)
        leet = self.tokenize(leet)
        normal = self.tokenize(text)

        leet = self.find(leet)
        normal = self.find(normal)
        
        return leet if leet else normal if normal else None
        
    def find(self, words: list[str]) -> str | None:
        """
        Find the first blacklisted word in the list of words.
        Returns the word if found, otherwise None.
        """
        for word in words:
            if word.lower() in WORD_BLACKLIST:
                return word
        return None
        
    def de_unicode(self, text: str) -> str:
        """
        Remove all non azAZ09 characters from the text.
        """
        return re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    
    def de_leet(self, text: str) -> str:
        """
        Convert leet speak to normal text.
        """
        for k, v in self.leet.items():
            text = text.replace(k, v)
        return text
    
    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize the text into words.
        """
        # Remove punctuation and split by whitespace
        text = text.lower()
        text = text.split(" ")
        return text
        
    
FlagMan = WordBlacklistManager()