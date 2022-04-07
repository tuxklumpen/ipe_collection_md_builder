import click

def process_line(line):
    line = line.strip()
    try:
        head, tail = line.split(" ", 1)
        match head:
            case "DESC:":
                return ("desc", tail)
            case "TITLE:":
                return ("title", tail)
    except ValueError:
        return None

def process_file(fp):
    incomment = False
    docitems = {}
    for line in fp.readlines():
        if line.startswith("<!--"):
            incomment = True

        if incomment:
            content = process_line(line)
            if content != None:
                docitems[content[0]] = content[1]

        if line.endswith("-->"):
            incomment = False

    click.echo(docitems)
    return docitems

def make_md_string(docs):
    md_lines = []
    for doc in docs:
        md_lines.append(
            f'# {doc["title"]}\n'
            f'{doc["desc"]}'
        )

    return "\n".join(md_lines)


@click.group()
def cli():
    pass

@cli.command()
@click.argument('stylefiles', nargs=-1)
@click.argument('mdfile', nargs=1)
def generate_doc(stylefiles, mdfile):
    if len(stylefiles) == 0:
        #TODO: implement default behavior to grep all styles in the directory
        click.echo("Error! No stylefile provided")
        return

    #TODO: Tests to only grep files with .isy extension

    docs = []
    for sf in stylefiles:
        with open(sf, "r") as fp:
            doc = process_file(fp)
            if doc:
                docs.append(doc)

    mdstring = make_md_string(docs)
    with open(mdfile, "w") as fp:
        fp.write(mdstring)
    