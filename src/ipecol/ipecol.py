import click
from ipecol.documentation import Documentation

# Entering point for all commands
@click.group()
def cli():
    pass

# The generate documentation command
@cli.command()
@click.argument('stylefiles', nargs=-1)
@click.argument('mdfile', nargs=1)
def generate_doc(stylefiles, mdfile):
    if len(stylefiles) == 0:
        #TODO: implement default behavior to grep all styles in the directory
        click.echo("Error! No stylefile provided")
        return

    #TODO: Tests to only grep files with .isy extension

    doc = Documentation()
    for stylefile in stylefiles:
        doc.add_stylefile(stylefile)

    doc.save_md(mdfile)