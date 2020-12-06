# use invoke and jinja template to automatically build environment


# use invoke to clean code
from invoke import run, task


@task(aliases=["fmt"])
def format(ctx):
    commands = ["black ./", "isort ./"]
    for command in commands:
        ctx.run(command)
    print("Done formatting!")


@task
def check(ctx):
    commands = ["black ./ --check", "isort ./ --check-only", "flake8 ./"]
    for command in commands:
        ctx.run(command)
    print("Done checking!")