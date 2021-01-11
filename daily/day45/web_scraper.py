import logging
import os
from typing import NamedTuple

import requests
from bs4 import BeautifulSoup

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)

SAVE_FILE_LOC = "./daily/day45/top_100_movies.txt"


class HackNews(NamedTuple):
    title: str
    link: str
    upvote: int


def get_latest_hack_news():
    # by default website returns 30 news
    response = requests.get("https://news.ycombinator.com/news")
    soup = BeautifulSoup(response.text, "html.parser")
    news = []
    for a_tag, s_tag in zip(
        soup.find_all("a", class_="storylink"), soup.find_all("span", class_="score")
    ):
        news.append(
            HackNews(a_tag.text, a_tag.get("href"), int(s_tag.text.split(" ")[0]))
        )
    return sorted(news, key=lambda x: x.upvote, reverse=True)


def clean_title(title: str):
    return title.split(")", 1)[-1].split(":", 1)[-1].strip()


def get_top_movies_empire():
    response = requests.get(
        "https://www.empireonline.com/movies/features/best-movies-2/"
    )
    soup = BeautifulSoup(response.text, "html.parser")
    movie_list = []
    for title_tag in soup.find_all("h3", class_="title"):
        movie_list.append(clean_title(title_tag.text))
    with open(SAVE_FILE_LOC, "w") as f:
        for idx, movie in enumerate(reversed(movie_list)):
            f.write(f"{idx + 1}. {movie}\n")
    logger.info(f"finished saving movies {len(movie_list)} to file {SAVE_FILE_LOC}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    # news = get_latest_hack_news()
    # print(news)
    get_top_movies_empire()
