# use invoke and jinja template to automatically build environment


# use invoke to clean code
from invoke import task


@task(aliases=["fmt"])
def format(ctx):
    commands = [
        "black ./",
        "isort ./",
        "autoflake -i -r --remove-unused-variables --remove-all-unused-imports ./",
    ]
    for command in commands:
        ctx.run(command)
    print("Done formatting!")


@task
def check(ctx):
    commands = ["black ./ --check", "isort ./ --check-only", "flake8 ./"]
    for command in commands:
        ctx.run(command)
    print("Done checking!")


@task(aliases=["dev"])
def develop(ctx):
    commands = ["python setup.py develop"]
    for command in commands:
        ctx.run(command)
    print("Package ready for development")
