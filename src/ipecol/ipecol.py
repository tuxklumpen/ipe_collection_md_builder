import click
import pathlib
import json
import tempfile as tmp
import shutil
import os
import logging
import tomli as tl
from git import Repo
from ipecol.documentation import Documentation

def _generate_doc(stylefiles, mdfile, svgpath, renderhints, renderfile=pathlib.Path("render.ipe"), keeprender=False, testing=False):
    if not svgpath:
        mdoutpath = pathlib.Path(mdfile.name).parent
        svgpath = mdoutpath
        
    hints = {}
    if renderhints:
        with open(renderhints, 'rb') as f:
            hints = json.load(f)
    
    doc = Documentation(svgpath, renderfile, hints)
    if stylefiles.is_file():
        doc.add_stylefile(stylefiles)
    else:
        for sfpath in stylefiles.iterdir():
            if sfpath.suffix == ".isy":
                doc.add_stylefile(sfpath)

    if testing:
        doc.set_testing_paths(svgpath)
    
    doc.save_md(mdfile)
    
    if not keeprender: 
        renderfile.unlink()
        
# Entering point for all commands
@click.group()
def cli():
    pass

# Only for debugging purposes now
# The generate documentation command
@cli.command()
@click.option('--renderfile', type = click.Path(path_type = pathlib.Path, writable = True, dir_okay = False), default = pathlib.Path("render.ipe"))
@click.option('--keeprender/--deleterender', default = False)
@click.option('--testing/--notesting', default = False)
@click.option('--renderhints', type = click.Path(path_type=pathlib.Path, dir_okay=False))
@click.option('--svgpath', type = click.Path(exists = True, path_type = pathlib.Path, writable = True))
@click.argument('stylefiles', type = click.Path(exists = True, path_type = pathlib.Path))
@click.argument('mdfile', type = click.File('wb'))
def generate_doc(stylefiles, mdfile, svgpath, renderfile, keeprender, testing, renderhints):
    _generate_doc(stylefiles, mdfile, svgpath, renderfile, keeprender, testing, renderhints)
    
# Command to update the whole repo
@cli.command()
@click.option('-c', '--config', type=click.Path(path_type=pathlib.Path, dir_okay=False), help="The config file in toml format.")
@click.option('-r', '--renderhints', type = click.Path(path_type=pathlib.Path, dir_okay=False), default=None, help="A renderhints file overwriting the on in the config file.")
@click.option('-g', '--repopath', type=click.Path(exists=True, path_type=pathlib.Path, file_okay=False), default=None, help="The path to the local GIT repo of the ipe collection overwriting the on in the config file.")
def update(repopath, config, renderhints):
    cfg = None
    with open(config, "rb") as f:
        cfg = tl.load(f)["config"]
    
    if not repopath:
        repopath = pathlib.Path(cfg["repository"])
        
    if not renderhints:
        renderhints = pathlib.Path(cfg["renderhints"])
        
    generatefor = cfg["directories"]
    
    logging.basicConfig(level=logging.INFO)
    repo = Repo(repopath)
    assert not repo.bare
    
    for style in generatefor:
        logging.info(f"Updating documentation for {style}")
        stylefiledir = pathlib.Path(repopath / style)
        assert stylefiledir.exists()
        
        with tmp.TemporaryDirectory() as tdir:
            # Make temporary directory
            tpath = pathlib.Path(tdir)
            mdpath = tpath / "README.md"
            svgpath = tpath / "svg"
            svgpath.mkdir()
            
            logging.info("Creating documentation.")
            with open(mdpath, "wb") as mdfile:
            # Generate new readme and svg in there
                _generate_doc(stylefiles=stylefiledir, mdfile=mdfile, svgpath=svgpath, renderhints=renderhints)
            
            # cp readme to repo
            logging.info("Copying README.md.")
            newmd = shutil.copy2(mdpath, stylefiledir)
            repo.index.add(stylefiledir, newmd)
            repo.index.commit(f"Updated README.md for {style}.")
            
            # cp assets to repo
            logging.info("Copying svgs.")
            repo.git.checkout("assets")
            svgs = []
            for svgfile in os.listdir(svgpath.absolute()):
                newsvg = shutil.copy2(svgpath / svgfile, stylefiledir)
                svgs.append(newsvg)
                logging.info(newsvg)
                
            repo.index.add(stylefiledir, newsvg)
            repo.index.commit(f"Updated svgs for {style}.")
            repo.git.checkout("development")
    
    repo.git.push()
    repo.git.checkout("assets")
    repo.git.push('origin', 'assets')       
    repo.git.checkout("development") 