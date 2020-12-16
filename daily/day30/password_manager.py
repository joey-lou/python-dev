import json
from collections import Counter
from tkinter import *
from tkinter import messagebox
from typing import Dict

from daily.day29.password_manager import PasswordManager


class SmartPasswordManager(PasswordManager):
    FILE_LOC = "./daily/day30/passwords.json"
    WEB_ENTRY_LENGTH = USER_ENTRY_LENGTH = PASSWORD_ENTRY_LENGTH = 25
    SIMILARITY_THRESHOLD = 0.5

    def __init__(self, root: Tk):
        super().__init__(root)

        # add search button
        Button(root, text="Search", command=self.search_passwords).grid(
            column=2, row=1, sticky=E
        )

    def _read_records(self,) -> Dict:
        try:
            with open(self.FILE_LOC, "r") as json_file:
                passwords = json.load(json_file)
            return passwords
        except FileNotFoundError:
            return {}

    @staticmethod
    def _calc_similarity_between(str_a, str_b):
        """ this can be an interesting problem by iteself:
            how do we evaluate similarity between two strings?
            there are many possibilities, here we choose a dumb implementation whereby
            we count the number of matched characters
            NOTE: here we assume comparing a against b, hence using b.length as denominator
        """
        counter_b = Counter(str_b)
        cnt = 0
        for k, c in Counter(str_a).items():
            cnt += min(counter_b[k], c)
        return cnt / len(str_b)

    def _yield_similar_records(self, records, website):
        # TODO: return in order of similarity
        for web, user_psw in records.items():
            if self._calc_similarity_between(website, web) > self.SIMILARITY_THRESHOLD:
                yield {web: user_psw}

    def search_passwords(self):
        # NOTE: can potentially add search based on username
        # TODO: add decorator to store generator
        records = self._read_records()
        web = self.web_entry.get()
        if web:
            similar_password = next(self._yield_similar_records(records, web), None)
            if similar_password:
                k, v = similar_password.popitem()
                messagebox.showinfo(
                    title="found a password!",
                    message=f"website: {k}\nusername:{v['username']}\npassword:{v['password']}",
                )

    # override original simple file save with json write
    def _save_to_file(self, web, user, psw):
        records = self._read_records()
        records.update({web: {"username": user, "password": psw}})
        with open(self.FILE_LOC, "w") as json_file:
            json.dump(records, json_file, indent=4)


if __name__ == "__main__":
    root = Tk()
    SmartPasswordManager(root)
    root.mainloop()
