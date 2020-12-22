"""
1. make class for making requests
2. add UI components
3. add mechanisms for interactions
"""
import html
import json
import logging
from tkinter import *
from typing import Optional

import requests
from pydantic import BaseModel

APP_NAME = "riddler"
logger = logging.getLogger(APP_NAME)


class TrueFalse(BaseModel):
    category: str
    question: str
    difficulty: str
    answer: bool


class QuizGetter:
    DEFAULT_AMOUNT = 10
    BASE_URL = "https://opentdb.com/api.php?type=boolean"

    FILM = 11
    ANIME = 31
    CATEGORIES = {FILM: "FILM", ANIME: "ANIME", None: "ANY"}
    CATEGORY_TO_NUM = {"FILM": FILM, "ANIME": ANIME, "ANY": None}

    def __init__(self, category: Optional[int] = None, amount: Optional[int] = None):
        # set instance variable at startup
        self._category = category
        self._amount = amount or self.DEFAULT_AMOUNT
        self._questions = None

    @staticmethod
    def _form_api_url(amount: int = 10, category: Optional[int] = 0):
        url = QuizGetter.BASE_URL + f"&amount={amount}"
        if category:
            url += f"&category={category}"
        return url

    def _get_trivias(self,):
        """ Get trivias using current settings
        """
        url = self._form_api_url(self.amount, self.category)
        logger.info(f"getting new trivias using url: {url}")
        response = requests.get(url)
        response.raise_for_status()  # check status
        for t in json.loads(response.text)["results"]:
            t["answer"] = True if t["correct_answer"] == "True" else False
            t["question"] = html.unescape(t["question"])
            yield TrueFalse(**t)

    @property
    def amount(self) -> int:
        return self._amount

    @amount.setter
    def amount(self, val: int):
        self._amount = val

    @property
    def category(self) -> int:
        return self._category

    @property
    def category_str(self) -> str:
        return self.CATEGORIES[self.category]

    @category.setter
    def category(self, val: int):
        assert val in self.CATEGORIES, f"available choices are {self.CATEGORIES}"
        self._category = val

    def refresh(self):
        self._questions = self._get_trivias()
        logger.info("refreshed question list")

    def next_question(self):
        return next(self._questions, None)


class Riddler:
    """ 
    A riddler that asks you true/false trivia questions
    """

    DEFAULT_CRED_PATH = "./secret/creds.json"  # user specific path
    RIDDLER_IMG = "./daily/day34/riddler.png"
    TRUE_IMG = "./daily/day34/true.png"
    FALSE_IMG = "./daily/day34/false.png"

    TITLE_COLOR = "#fdb827"
    THEME_COLOR = "#a3d2ca"
    BOARD_COLOR = "#f8f1f1"
    FONT_NAME = "Courier"
    TEXT_COLOR = "#433d3c"
    SCORE_COLOR = "#db6400"

    def __init__(self, root: Tk, quiz_handler: QuizGetter):
        self.qhndl = quiz_handler
        self.cq: Optional[TrueFalse] = None  # track current question
        self._score = 0
        self._started = False

        root.title("Riddler")
        root.config(padx=20, pady=20, bg=self.THEME_COLOR)
        # topic-board
        self.label_topic = Label(
            root,
            text=self._get_category_statement(),
            font=(self.FONT_NAME, 15, "bold"),
            fg=self.SCORE_COLOR,
            bg=self.THEME_COLOR,
        )
        self.label_topic.grid(column=0, row=0, columnspan=2, padx=10, pady=10)

        # score-board
        self.label_score = Label(
            root,
            text=self._get_score_statement(),
            font=(self.FONT_NAME, 15, "bold"),
            fg=self.SCORE_COLOR,
            bg=self.THEME_COLOR,
        )
        self.label_score.grid(column=2, row=0, columnspan=2, padx=10, pady=10)

        # main question board
        canvas = Canvas(
            root, height=300, width=300, bg=self.BOARD_COLOR, highlightthickness=0
        )
        self.images = [
            PhotoImage(file=self.RIDDLER_IMG),
            PhotoImage(file=self.TRUE_IMG),
            PhotoImage(file=self.FALSE_IMG),
        ]
        canvas.grid(column=0, row=1, columnspan=4)
        self.main_text = canvas.create_text(
            40,
            50,
            text="Ready to start?!",
            fill=self.TITLE_COLOR,
            font=(self.FONT_NAME, 35, "bold"),
            anchor=NW,
            width=250,
        )
        self.riddler = canvas.create_image(
            0, 0, image=self.images[0], anchor=NW, state="hidden"
        )
        self.canvas = canvas

        # add buttons
        self.button_true = Button(
            root,
            image=self.images[1],
            bd=0,
            highlightthickness=0,
            command=lambda: self.answer_question(True),
        )
        self.button_false = Button(
            root,
            image=self.images[2],
            bd=0,
            highlightthickness=0,
            command=lambda: self.answer_question(False),
        )
        self.button_refresh = Button(
            root,
            text="Start",
            command=self.refresh,
            bd=0,
            highlightthickness=0,
            height=2,
            width=5,
        )
        self.button_anime = Button(
            root,
            text="Anime",
            command=lambda: self.set_category(self.qhndl.ANIME),
            bd=0,
            highlightthickness=0,
            height=2,
            width=5,
        )
        self.button_film = Button(
            root,
            text="Film",
            command=lambda: self.set_category(self.qhndl.FILM),
            bd=0,
            highlightthickness=0,
            height=2,
            width=5,
        )

        self.button_true.grid(column=0, row=2, columnspan=2, sticky=W, pady=10)
        self.button_false.grid(column=2, row=2, columnspan=2, sticky=E, pady=10)
        self.button_refresh.grid(column=0, row=3)
        self.button_anime.grid(column=2, row=3)
        self.button_film.grid(column=3, row=3)

    def set_category(self, category: Optional[int]):
        if self.qhndl.category == category:
            return
        self.qhndl.category = category
        self._update_category()
        self.refresh()

    def refresh(self,):
        self.canvas.itemconfig(self.riddler, state="hidden")
        self.button_refresh.config(text="Refresh")
        logger.info("starting a new quiz session..")
        self.qhndl.refresh()
        self.cq = self.qhndl.next_question()
        self._update_quiz()
        self._update_score(0)
        self._started = True

    def answer_question(self, answer: bool):
        if not self._started:
            return
        self._check_answer(answer)
        self.cq = self.qhndl.next_question()
        if not self.cq:
            self._show_end_screen()
        else:
            self._update_quiz()

    def _show_end_screen(self):
        self.canvas.coords(self.main_text, 40, 50)
        text = "Good Job!" if self._score > 5 else "Please try again!"
        if self._score == self.qhndl.amount:
            # show hidden riddler pic for special occasion only
            self.canvas.itemconfig(self.riddler, state="normal")
        self.canvas.itemconfig(
            self.main_text,
            text=text,
            fill=self.TITLE_COLOR,
            font=(self.FONT_NAME, 35, "bold"),
            anchor=NW,
            width=250,
        )
        self._started = False

    def _update_category(self):
        self.label_topic.config(text=self._get_category_statement())

    def _update_score(self, score: int):
        self._score = score
        self.label_score.config(text=self._get_score_statement())

    def _check_answer(self, answer: bool):
        if self.cq.answer == answer:
            self._update_score(self._score + 1)

    def _get_score_statement(self):
        return f"Score: {self._score}"

    def _get_category_statement(self):
        return f"Category: {self.qhndl.category_str}"

    def _update_quiz(self):
        self.canvas.coords(self.main_text, 30, 50)
        self.canvas.itemconfig(
            self.main_text,
            text=self.cq.question,
            fill=self.TEXT_COLOR,
            font=(self.FONT_NAME, 20),
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{__name__}[%(levelname)s][%(asctime)s]: %(message)s",
    )

    root = Tk()
    qg = QuizGetter()
    rid = Riddler(root, qg)
    root.mainloop()
