from tkinter import *
from tkinter import ttk


class WeightConverter:
    def __init__(self, root):

        root.title("Pound to Kilograms")

        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # create input and output cells
        self.pound = StringVar()
        pound_entry = ttk.Entry(mainframe, width=7, textvariable=self.pound)
        pound_entry.grid(column=1, row=1, sticky=(W, E))
        self.kilogram = StringVar()

        ttk.Label(mainframe, text="lb").grid(column=2, row=1, sticky=W)
        ttk.Label(mainframe, text="=").grid(column=3, row=1, sticky=(W, E))
        ttk.Label(mainframe, textvariable=self.kilogram).grid(
            column=4, row=1, sticky=(W, E)
        )
        ttk.Label(mainframe, text="kg").grid(column=5, row=1, sticky=E)
        ttk.Button(mainframe, text="Calculate", command=self.calculate).grid(
            column=4, row=2, sticky=(W, E)
        )

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        pound_entry.focus()
        root.bind("<Return>", self.calculate)

    def calculate(self, *args):
        try:
            value = float(self.pound.get())
            self.kilogram.set(round(value * 0.45359237, 2))
        except ValueError:
            pass


if __name__ == "__main__":
    root = Tk()
    WeightConverter(root)
    root.mainloop()
