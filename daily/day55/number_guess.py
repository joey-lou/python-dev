import logging
from functools import wraps
from random import randint

from flask import Flask

app = Flask(__name__)
logger = logging.getLogger(__name__)
secret = randint(0, 9)
logger.info(f"Secret number is {secret}!")


def html_style(style: str):
    """ style html text with bold/ highlight etc.
        by wrapping returned string with desired achor tag
    """
    styles = {
        "bold": "b",
        "itallic": "i",
        "small": "small",
        "highlight": "mark",
        "title": "h1",
    }

    def wrapper(func):
        tag = styles[style]

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            return f"<{tag}>{func(*args, **kwargs)}</{tag}>"

        return wrapped_func

    return wrapper


@app.route("/")
@html_style("title")
def home():
    return (
        'Guess a number from 1 - 10! <iframe src="https://giphy.com/gifs/3o7aCSPqXE5C6T8tBC/html5" '
        'width="480" height="480" frameBorder="0" class="giphy-embed"/>'
    )


@app.route("/<int:number>")
@html_style("title")
def menu(number):
    if number > secret:
        return 'Too high, guess lower <img src="https://media.giphy.com/media/3o6ZtaO9BZHcOjmErm/giphy.gif"/>'
    elif number < secret:
        return (
            'Too low <img src="https://media.giphy.com/media/jD4DwBtqPXRXa/giphy.gif"/>'
        )
    return (
        'Right! <img src="https://media.giphy.com/media/xTiTnf9SCIVk8HIvE4/giphy.gif"/>'
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{__name__}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    app.run(debug=True)
