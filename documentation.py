from os import path
from bs4 import BeautifulSoup, Comment
from dataclasses import dataclass, field
from jinja_helper import get_template
from example_generator import examples_from_stylefile, Example

MD_TEMPLATE_FILE = "documentation.jinja2"
    
@dataclass
class StylefileDoc:
    title : str
    name : str
    folder : str
    description : str
    examples : list[Example]

@dataclass
class Documentation:
    docs : list[StylefileDoc] = field(default_factory = list)

    # TODO: Error handling 
    def add_stylefile(self, stylefile):
        doc = get_documentation(stylefile)
        if doc:
            self.docs.append(doc)

    def save_md(self, mdfilepath):
        template = get_template(MD_TEMPLATE_FILE)
        output = template.render({"documentation" : self})

        with open(mdfilepath, "w") as fp:
            fp.write(output)

# Process one line of the documentation comment
def process_doc_line(line):
    line = line.strip()
    try:
        head, tail = line.split(" ", 1)
        match head:
            case "DESC:":
                return ("description", tail)
            case "TITLE:":
                return ("title", tail)
    except ValueError:
        return None

def process_comment(comment):
    docitems = {}
    lines = comment.split("\n")
    for line in lines:
        if len(line) > 0:
            docitem = process_doc_line(line)
            if docitem:
                docitems[docitem[0]] = docitem[1]

    return docitems

def find_docitems(soup):
    comments = soup.find_all(string = lambda text: isinstance(text, Comment))
    docitems = None
    for comment in comments:
        docitems = process_comment(comment)

    return docitems

# Process one stylesheet file
def get_documentation(stylefilepath):
    docitems = None
    with open(stylefilepath, "r") as fp:
        docitems = _get_docitems_and_examples(fp)
    
    if docitems:
        docitems["name"] = path.basename(stylefilepath)
        docitems["folder"] = path.basename(path.dirname(stylefilepath))

    return StylefileDoc(**docitems)
        
def _get_docitems_and_examples(fp):
    soup = BeautifulSoup(fp, 'xml')
    docitems = find_docitems(soup)
    docitems["examples"] = examples_from_stylefile(soup)

    return docitems