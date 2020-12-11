import os
import random
from tkinter import *
from tkinter import messagebox


class PasswordManager:
    FILE_LOC = "./daily/day29/passwords.txt"
    DEFAULT_USER = "boo@ya.com"
    WEB_ENTRY_LENGTH = USER_ENTRY_LENGTH = 35
    PASSWORD_ENTRY_LENGTH = 20
    PASSWORD_LENGTH = 15

    def __init__(self, root: Tk):
        root.title("Password Manager")
        root.config(padx=20, pady=20)
        canvas = Canvas(root, height=200, width=200)
        lock_img = PhotoImage(file="./daily/day29/logo.png")  # path relative to package
        canvas.create_image(100, 100, image=lock_img)  # default to center rule
        canvas.grid(column=1, row=0)
        canvas.img = lock_img

        # add static UI elements
        self._draw_web_components(root)
        self._draw_user_components(root)
        self._draw_password_components(root)

        # add buttons
        Button(root, text="Generate", command=self.generate_password).grid(
            column=2, row=3, sticky=E
        )
        Button(root, text="Add", command=self.add_password).grid(
            column=2, row=4, sticky=E
        )
        Button(root, text="Clear", command=self.reset_app).grid(
            column=2, row=5, sticky=E
        )
        Button(root, text="Delete All", command=self.reset_passwords).grid(
            column=0, row=5, sticky=E
        )

        self.reset_app()

    def _draw_web_components(self, root):
        Label(root, text="Website:").grid(column=0, row=1, sticky=E)
        self.web_entry = Entry(root, width=self.WEB_ENTRY_LENGTH)
        self.web_entry.grid(column=1, row=1, columnspan=2, sticky=W)

    def _draw_user_components(self, root):
        Label(root, text="Email or Username:").grid(column=0, row=2, sticky=E)
        self.user_entry = Entry(root, width=self.USER_ENTRY_LENGTH)
        self.user_entry.grid(column=1, row=2, columnspan=2, sticky=W)

    def _draw_password_components(self, root):
        Label(root, text="Password:").grid(column=0, row=3, sticky=E)
        self.password_entry = Entry(root, width=self.PASSWORD_ENTRY_LENGTH)
        self.password_entry.grid(column=1, row=3, sticky=W)

    def reset_app(self):
        self.web_entry.delete(0, END)
        self.user_entry.delete(0, END)
        self.password_entry.delete(0, END)
        self.web_entry.focus()
        self.user_entry.insert(END, self.DEFAULT_USER)

    def reset_passwords(self):
        if os.path.exists(self.FILE_LOC):
            os.remove(self.FILE_LOC)

    def generate_password(self):
        self.password_entry.delete(0, END)
        lower, upper = 33, 126
        random_strs = [
            chr(random.randint(lower, upper)) for _ in range(self.PASSWORD_LENGTH)
        ]
        random.shuffle(random_strs)
        psw = "".join(random_strs)
        self.password_entry.insert(END, psw)

    @staticmethod
    def _pad_output(text: str, is_small: bool = False):
        expected_length = (
            PasswordManager.PASSWORD_ENTRY_LENGTH
            if is_small
            else PasswordManager.WEB_ENTRY_LENGTH
        )
        current_length = len(text)
        return text + (expected_length - current_length) * " "

    def _save_to_file(self, web, user, psw):
        with open(self.FILE_LOC, "a") as f:
            f.write(
                f"{self._pad_output(web)}"
                f"{self._pad_output(user)}"
                f"{self._pad_output(psw, True)}\n"
            )

    def add_password(self):
        web = self.web_entry.get()
        user = self.user_entry.get()
        psw = self.password_entry.get()

        if web and user and psw:
            is_ok = messagebox.askokcancel(
                title="confirm",
                message=(f"     web: {web}\n" f"    user: {user}\n" f"password: {psw}"),
            )
            if is_ok:
                self._save_to_file(web, user, psw)
                self.reset_app()
        else:
            messagebox.showerror(title="error", message="Please fill out all fields")


if __name__ == "__main__":
    root = Tk()
    PasswordManager(root)
    root.mainloop()
