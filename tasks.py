# use invoke and jinja template to automatically build environment


import re
from platform import python_version

from invoke import UnexpectedExit, task


def parse_failed_packages(stderr: str):
    matches = re.findall(
        r"current channels:\s*((?:- |\w+=*[1-9\.]*)+)\s*Current channels",
        stderr.replace("\n", ""),
    )[0]
    return matches.rsplit("- ")[1:]


# use invoke to clean code
@task(help="installs all dependency packages")
def bootstrap(ctx, python=python_version(), pip=False):
    def install_with_pip(*packages):
        ctx.run(f"pip install {' '.join(packages)}", echo=True)

    def install(*packages):
        try:
            ctx.run(f"conda install {' '.join(packages)}", echo=True)
        except UnexpectedExit as e:
            if "PackagesNotFoundError" in e.result.stderr:
                failed_packages = parse_failed_packages(e.result.stderr)
                ctx.run(
                    f"conda install {' '.join(set(packages) - set(failed_packages))} ",
                    echo=True,
                )
                install_with_pip(failed_packages)
                ctx.run(f"pip install {' '.join(failed_packages)}", echo=True)
            else:
                raise e

    install_func = install_with_pip if pip else install

    try:
        import jinja2
        import yaml
    except ModuleNotFoundError:
        install_func("jinja2", "pyyaml")
        import jinja2
        import yaml

    with open("meta.yaml") as f:
        template = jinja2.Template(f.read())

    meta_yaml = yaml.safe_load(template.render(python=python))
    dev_packages = meta_yaml["requirements"]["develop"]
    run_packages = meta_yaml["requirements"]["run"]
    install_func(*dev_packages, *run_packages)


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
    commands = ["black ./ --check", "isort ./ --check-only", "autoflake -c -r ./"]
    for command in commands:
        ctx.run(command)
    print("Done checking!")


@task(aliases=["dev"])
def develop(ctx):
    commands = ["python -m pip install --editable ."]
    for command in commands:
        ctx.run(command)
    print("Package ready for development")
