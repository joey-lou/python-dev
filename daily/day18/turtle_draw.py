import turtle as tt


def go_home(tim: tt.Turtle):
    tim.clear()
    tim.penup()
    tim.home()
    tim.pendown()


def run_sketch_by_keyboard(tim: tt.Turtle, canvas: tt.Screen):
    canvas.listen()
    min_distance = 10
    min_angle = 10
    canvas.onkey(key="w", fun=lambda: tim.fd(min_distance))
    canvas.onkey(key="a", fun=lambda: tim.lt(min_angle))
    canvas.onkey(key="s", fun=lambda: tim.fd(-min_distance))
    canvas.onkey(key="d", fun=lambda: tim.lt(-min_angle))
    canvas.onkey(key="space", fun=lambda: go_home(tim))


def main():
    tim = tt.Turtle(shape="turtle")
    canvas = tt.Screen()
    run_sketch_by_keyboard(tim, canvas)
    canvas.exitonclick()


if __name__ == "__main__":
    main()
