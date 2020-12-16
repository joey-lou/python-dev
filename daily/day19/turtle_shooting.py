import logging
import math
import os
import random
import time
import turtle as tt

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)
logging.basicConfig(
    level=logging.DEBUG, format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s"
)

BOARD_HEIGHT = 200
BOARD_WIDTH = 200


class Target(tt.Turtle):
    X_MAX = BOARD_WIDTH
    Y_MAX = BOARD_HEIGHT
    TARGET_SIZE = 0.5

    def __init__(self, *args, shape="square", **kwargs):
        super().__init__(*args, shape=shape, **kwargs)
        self.penup()
        self.hideturtle()
        self.turtlesize(stretch_wid=self.TARGET_SIZE, stretch_len=self.TARGET_SIZE)
        self.reset()

    def reset(self,):
        self.hideturtle()
        x = random.randint(-self.X_MAX, self.X_MAX)
        y = random.randint(-self.X_MAX, self.X_MAX)
        self.setposition(x, y)
        logger.debug(f"reseting target to {x}, {y}")
        self.showturtle()


class Bullet(tt.Turtle):
    BULLET_SIZE = 0.2

    def __init__(self, *args, shape="circle", **kwargs):
        super().__init__(*args, shape=shape, **kwargs)
        self.hideturtle()
        self.penup()
        self.turtlesize(stretch_wid=self.BULLET_SIZE, stretch_len=self.BULLET_SIZE)

    def shoot(self, x: float, y: float, angle: float, length: float):
        # reset bullet to certain position
        self.setpos(x, y)
        self.setheading(angle)
        self.showturtle()
        self.forward(length)
        self.clear()
        self.hideturtle()


class Scorer(tt.Turtle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.penup()
        self.hideturtle()
        self.setpos(0, BOARD_HEIGHT)
        self.write(
            "Start!\nUse WASD to move the space turtle\nPress Space to shoot",
            align="center",
            font=("Arial", 15, "normal"),
        )
        self.score = 0

    def set_score(self, num: int):
        self.score = num
        self.display_score()

    def add_score(self, num: int):
        self.score += num
        self.display_score()

    def display_score(self):
        self.clear()
        self.write(f"Score {self.score}", font=("Arial", 15, "normal"))


class Shooter(tt.Turtle):
    MIN_DIST = 10
    MIN_AGL = 10
    PROXIMITY = (
        10  # the largest permissable distance between bullet and target to score
    )
    REACT_TIME = 1000

    def __init__(
        self,
        bullet: Bullet,
        target: Target,
        scorer: Scorer,
        shoot_range: int = 100,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.bullet = bullet
        self.target = target
        self.scorer = scorer
        self.max_shoot_range = shoot_range
        self.penup()
        self._hit = False
        self._left_pressed = False
        self._right_pressed = False
        self._forward_pressed = False
        self._backward_pressed = False

    def _turn_left(self, call_num=0):
        if call_num == 0:
            self._left_pressed = True
        if self._left_pressed:
            logger.debug(f"left turning {call_num}")
            self.lt(self.MIN_AGL)
            self.screen.ontimer(lambda: self._turn_left(call_num + 1), self.REACT_TIME)

    def _turn_right(self, call_num=0):
        if call_num == 0:
            self._right_pressed = True
        if self._right_pressed:
            logger.debug(f"right turning {call_num}")
            self.lt(-self.MIN_AGL)
            self.screen.ontimer(lambda: self._turn_right(call_num + 1), self.REACT_TIME)

    def _move_forward(self, call_num=0):
        if call_num == 0:
            self._forward_pressed = True
        if self._forward_pressed:
            logger.debug(f"going forward {call_num}")
            self.fd(self.MIN_DIST)
            self.screen.ontimer(
                lambda: self._move_forward(call_num + 1), self.REACT_TIME
            )

    def _move_backward(self, call_num=0):
        if call_num == 0:
            self._backward_pressed = True
        if self._backward_pressed:
            logger.debug(f"moving backward {call_num}")
            self.fd(-self.MIN_DIST)
            self.screen.ontimer(
                lambda: self._move_backward(call_num + 1), self.REACT_TIME
            )

    def _cancel_left(self):
        logger.debug("cancel left")
        self._left_pressed = False

    def _cancel_right(self):
        logger.debug("cancel right")
        self._right_pressed = False

    def _cancel_forward(self):
        logger.debug("cancel forward")
        self._forward_pressed = False

    def _cancel_backward(self):
        logger.debug("cancel backward")
        self._backward_pressed = False

    def _calc_angle(self):
        """ calcualte angle between shooter (bullet) and target
        """
        x, y = self.pos()
        x_t, y_t = self.target.pos()
        angle = math.atan2(y_t - y, x_t - x)
        return self.heading() - math.degrees(angle)

    def _calc_trajectory(self, shoot_range):
        """ calculate the path of bullet, see if it will be close to target
            simply check for the angle between bullet's heading and our target, with shooter as point of ref
            expected shortest distance between bullet and target = sin(angle)
            the distance bullet has to travel to get to that shortest-dist point = cos(angle)
        """
        angle = self._calc_angle()
        radians = math.radians(angle)
        dist = self.distance(self.target)
        shortest_dist = abs(math.sin(radians) * dist)
        expected_travel = math.cos(radians) * dist
        logger.debug(
            f"angle={angle:.2f}\tdist={dist:.2f}\tshortest_dist={shortest_dist:.2f}\ttravel={expected_travel:.2f}"
        )

        if (
            shortest_dist < self.PROXIMITY
            and expected_travel > 0
            and expected_travel < shoot_range
        ):
            logger.debug("on successful hit trajectory")
            self._hit = True
            return expected_travel
        else:
            # no luck
            return shoot_range

    def _shoot(self,):
        logger.debug("trigger shooting")
        angle = self.heading()
        x, y = self.pos()
        dist = self._calc_trajectory(self.max_shoot_range)
        self.bullet.shoot(x, y, angle, dist)
        if self._hit:
            self.target.reset()
            self.scorer.add_score(1)
            self._hit = False

    def start(self):
        logger.info("starting shooter keybind")
        # bind to keyboard
        self.penup()
        self.screen.onkeypress(key="w", fun=self._move_forward)
        self.screen.onkeypress(key="a", fun=self._turn_left)
        self.screen.onkeypress(key="s", fun=self._move_backward)
        self.screen.onkeypress(key="d", fun=self._turn_right)
        self.screen.onkey(key="space", fun=self._shoot)
        self.screen.onkey(key="h", fun=self.home)

        self.screen.onkeyrelease(key="w", fun=self._cancel_forward)
        self.screen.onkeyrelease(key="a", fun=self._cancel_left)
        self.screen.onkeyrelease(key="s", fun=self._cancel_backward)
        self.screen.onkeyrelease(key="d", fun=self._cancel_right)

        self.scorer.set_score(0)


def main():
    # initialize board
    screen = tt.Screen()

    tt.screensize(BOARD_WIDTH, BOARD_HEIGHT)
    tt.title("Turtle Shooter")

    bullet = Bullet()
    target = Target()
    scorer = Scorer()

    # start game
    shooter = Shooter(bullet=bullet, target=target, scorer=scorer, shape="turtle")
    time.sleep(1)
    screen.listen()
    shooter.start()

    # exit on click
    tt.exitonclick()


if __name__ == "__main__":
    main()
