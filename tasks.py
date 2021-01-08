# use invoke and jinja template to automatically build environment


from platform import python_version

# use invoke to clean code
from invoke import task


@task(help="installs all dependency packages")
def bootstrap(ctx, python=python_version()):
    def install(*packages):
        ctx.run("conda install -qy " + " ".join(packages), echo=True)

    try:
        import jinja2
        import yaml
    except ModuleNotFoundError:
        install("jinja2", "pyyaml")
        import jinja2
        import yaml

    with open("meta.yaml") as f:
        template = jinja2.Template(f.read())

    meta_yaml = yaml.safe_load(template.render(python=python))
    dev_packages = meta_yaml["requirements"]["develop"]
    run_packages = meta_yaml["requirements"]["run"]
    install(*dev_packages, *run_packages)


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
