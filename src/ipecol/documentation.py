import json
import pathlib
from bs4 import BeautifulSoup, Comment
from dataclasses import dataclass, field
from ipecol.jinja_helper import get_template
from ipecol.example_generator import examples_from_stylefile, Example

MD_TEMPLATE_FILE = "documentation.jinja2"

@dataclass
class StylefileDoc:
    title : str
    description : str
    provided_by : [str]
    style_count : [int]
    style_types : [str]
    
    name : str
    
    examples : list[Example]
    
    def set_testing_path(self, svgpath):
        for example in self.examples:
            example.set_testing_path(svgpath)

@dataclass
class Documentation:
    svgpath : pathlib.Path
    renderfile : pathlib.Path
    hints : dict
    docs : list[StylefileDoc] = field(default_factory = list)
    testing : bool = False

    # TODO: Error handling 
    def add_stylefile(self, stylefile):
        doc = get_documentation(stylefile, self.svgpath, self.renderfile, self.hints)
        if doc:
            self.docs.append(doc)

    def save_md(self, mdfile):
        template = get_template(MD_TEMPLATE_FILE)
        output = template.render({"documentation" : self,
                                  "collapseat" : 10})

        mdfile.write(bytes(output, 'UTF-8'))
        
    def set_testing_paths(self, svgpath):
        self.testing=True
        for doc in self.docs:
            doc.set_testing_path(svgpath)

def process_comment(comment):
    comment = comment.strip()
    if not comment.startswith("ipecol"):
        return None
    
    docitems = {}
    comment = comment.replace("ipecol", "")
    return json.loads(comment)

def find_docitems(soup):
    comments = soup.find_all(string = lambda text: isinstance(text, Comment))
    docitems = None
    for comment in comments: 
        docitems = process_comment(comment)
        
        if docitems:
            break

    # TODO: Error handling if docitems is None

    return docitems

# Process one stylesheet file
def get_documentation(stylefilepath, svgpath, renderfile, hints):
    docitems = None
    with open(stylefilepath, "r") as fp:
        soup = BeautifulSoup(fp, 'xml')
        folder = stylefilepath.parent.name
        docitems = find_docitems(soup)
        docitems["examples"] = examples_from_stylefile(soup, svgpath, renderfile, folder, hints)
    
    if docitems:
        docitems["name"] = stylefilepath.name
        
    return StylefileDoc(**docitems)