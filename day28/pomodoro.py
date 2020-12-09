import datetime as dt
from enum import IntEnum
from tkinter import *
from tkinter import ttk


class WorkStatus(IntEnum):
    WORK = 0
    SHORT_BREAK = 1
    LONG_BREAK = 2


class Pomodoro:
    PINK = "#e2979c"
    RED = "#e7305b"
    GREEN = "#9bdeac"
    YELLOW = "#f7f5dd"
    FONT_NAME = "Courier"
    WORK_MIN = 0.1
    SHORT_BREAK_MIN = 0.1
    LONG_BREAK_MIN = 0.1
    FONT_SIZE = 35

    COLOR_ROTATION = [PINK, RED, YELLOW, GREEN]  # potentially rotate color pallete

    def __init__(self, root: Tk, image_loc: str = "tomato.png"):
        root.title("Pomodoro")
        root.config(padx=100, pady=50)
        self.root = root
        # set timer
        self.timer = ""
        self.checkmark = ""
        self._after_id = None

        self.title = Label(
            root,
            text="Pomodoro",
            fg=self.GREEN,
            font=(self.FONT_NAME, 40, "italic"),
            padx=20,
        )
        self.tomato = Canvas(root, width=250, height=250, highlightthickness=0)

        # draw out canvas elements
        tomato_bkg = PhotoImage(file=image_loc)
        self.tomato.create_image(25, 20, image=tomato_bkg, anchor=NW)
        self.tomato.img = tomato_bkg  # image garbage collector bug
        self.tomato_time = self.tomato.create_text(
            90,
            125,
            text=self.timer,
            fill="white",
            font=(self.FONT_NAME, 35, "bold"),
            anchor=NW,
        )

        self.start_button = Button(
            root,
            text="Start",
            command=lambda: self.count_down(int(self.WORK_MIN * 60), WorkStatus.WORK),
            highlightthickness=0,
        )
        self.reset_button = Button(
            root, text="Reset", command=self.reset, highlightthickness=0
        )

        self.checkmark_counts = Label(root, text=self.checkmark)

        # set grids
        self.title.grid(column=1, row=0)
        self.checkmark_counts.grid(column=1, row=2)
        self.tomato.grid(column=1, row=1)
        self.start_button.grid(column=0, row=2)
        self.reset_button.grid(column=2, row=2)

        self._set_background(self.COLOR_ROTATION[0])
        self._set_timer(0)
        self._set_checkmark(0)

    def _set_timer(self, seconds):
        self.timer = dt.time(0, seconds // 60, seconds % 60).strftime("%M:%S")
        self.tomato.itemconfig(self.tomato_time, text=self.timer)

    def _set_checkmark(self, count):
        self.checkmark = "✔" * count
        self.checkmark_counts.config(text=self.checkmark)

    def count_down(self, seconds, status: WorkStatus):
        if status == WorkStatus.WORK:
            if seconds > 0:
                self.title.config(text="  Work  ")
                self._set_timer(seconds)
                self._after_id = self.root.after(
                    1000, self.count_down, seconds - 1, WorkStatus.WORK
                )
            else:
                self._set_checkmark(1 + len(self.checkmark))
                is_short_break = len(self.checkmark) < 3
                self.title.config(text="Break")
                seconds = int(
                    (self.SHORT_BREAK_MIN if is_short_break else self.LONG_BREAK_MIN)
                    * 60
                )
                self._set_timer(seconds)
                self._after_id = self.root.after(
                    1000,
                    self.count_down,
                    seconds - 1,
                    WorkStatus.SHORT_BREAK if is_short_break else WorkStatus.LONG_BREAK,
                )
        elif status == WorkStatus.SHORT_BREAK:
            if seconds > 0:
                self.title.config(text="Break")
                self._set_timer(seconds)
                self._after_id = self.root.after(
                    1000, self.count_down, seconds - 1, WorkStatus.SHORT_BREAK
                )
            else:
                self.title.config(text="  Work  ")
                seconds = int(self.WORK_MIN * 60)
                self._set_timer(seconds)
                self._after_id = self.root.after(
                    1000, self.count_down, seconds - 1, WorkStatus.WORK
                )
        else:
            if seconds > 0:
                self.title.config(text="Break")
                self._set_timer(seconds)
                self._after_id = self.root.after(
                    1000, self.count_down, seconds - 1, WorkStatus.LONG_BREAK
                )
            else:
                self.title.config(text="Congrats!")

    def reset(self):
        self._set_timer(0)
        self._set_checkmark(0)
        self.root.after_cancel(self._after_id)

    def _set_background(self, bg_color):
        self.root.config(bg=bg_color)
        self.tomato.config(bg=bg_color)
        self.title.config(bg=bg_color)
        self.checkmark_counts.config(bg=bg_color)


if __name__ == "__main__":
    root = Tk()
    Pomodoro(root)
    root.mainloop()
