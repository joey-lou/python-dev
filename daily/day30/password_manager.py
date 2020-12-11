import os
import random
from tkinter import *
from tkinter import messagebox

from daily.day29.password_manager import PasswordManager

if __name__ == "__main__":
    root = Tk()
    PasswordManager(root)
    root.mainloop()
