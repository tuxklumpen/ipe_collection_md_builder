import subprocess
import inspect
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from jinja_helper import get_template
from abc import ABC, abstractmethod

IPE_TEMPLATE_FILE = "ipetemplate.jinja2"

@dataclass
class IpeOptions:
    stroke_color : str = "black"
    fill_color : str = "white"
    pen : str = "normal"
    mark_size : str = "normal"

class StylefileTagParser(ABC):
    def __init__(self, template, options = IpeOptions()):
        self.template = template
        self.options = options

    def _render_template(self, name):
        template = get_template(self.template)
        ipe = template.render({
            "name" : name,
            "options" : self.options
        })

        return ipe

    @abstractmethod
    def applies(self, tag):
        pass

    @abstractmethod
    def parse(self, tag):
        pass

class SymbolParser(StylefileTagParser):
    def __init__(self, symbolname, template, options = IpeOptions()):
        super().__init__(template, options)
        self.symbolname = symbolname

    def applies(self, tag):
        return tag.name == "symbol" and tag["name"].startswith(self.symbolname)

class MarkParser(SymbolParser):
    TEMPLATE = "mark.jinja2"

    def __init__(self, options = IpeOptions()):
        super().__init__("mark", MarkParser.TEMPLATE, options)
        
    def parse(self, tag):
        name = tag["name"]
        ipe = self._render_template(name)

        return {"type" : "mark", "name" : name, "ipe" : ipe}

class PropertyParser(StylefileTagParser):
    def __init__(self, propertyname, template, options = IpeOptions()):
        super().__init__(template, options)
        self.propertyname = propertyname

    def applies(self, tag):
        return tag.name == self.propertyname

class DashParser(PropertyParser):
    TEMPLATE = "dashstyle.jinja2"

    def __init__(self, options = IpeOptions()):
        super().__init__("dashstyle", DashParser.TEMPLATE, options)

    def parse(self, tag):
        name = tag["name"]
        self.options.pen = "ultrafat"
        ipe = self._render_template(name)

        return {"type" : "dash", "name" : name, "ipe" : ipe}

# #TODO: Implement
# class ColorParser(StylefileTagParser):
#     def applies(tag):
#         pass

#     def parse(tag):
#         pass

@dataclass
class Example:
    name: str
    picture_path: str

def get_name(ipe_name):
    return ipe_name.replace("/", "")

#TODO: Should be moved to some form of util component
def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])

def process_tag(tag):
    item = None
    for parser_cls in all_subclasses(StylefileTagParser):
        if not inspect.isabstract(parser_cls):
            parser = parser_cls()
            if parser.applies(tag):
                item = parser.parse(tag)

    return item

def examples_from_stylefile(soup):
    template = get_template(IPE_TEMPLATE_FILE)
    
    items = []
    for child in soup.ipestyle.children:
        if child != "\n":
            items.append(process_tag(child))

    template_variables = {
        "stylesheets" : [soup.ipestyle],
        "items" : items
    }

    #TODO: Should make a temporary file instead
    output = template.render(template_variables)
    with open("test.ipe", "w") as fp:
        fp.write(output)

    examples = []
    for item in items:
        page = item["name"]
        outfile = get_name(item["name"]) + ".svg"
        subprocess.run(["iperender", "-svg", "-page", page, "test.ipe", outfile])

        with open(outfile, "r+") as fp:
            figsoup = BeautifulSoup(fp, "xml")
            figsoup.svg["style"] = "background-color:white"
            fp.seek(0)
            fp.write(figsoup.prettify())

        examples.append(Example(page, outfile))

    return examples