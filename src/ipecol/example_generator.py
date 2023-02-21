import subprocess
import inspect
import pathlib
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from ipecol.jinja_helper import get_template
from abc import ABC, abstractmethod

IPE_TEMPLATE_FILE = "ipetemplate.jinja2"
IPE_RENDER_FILE = "render.ipe"

@dataclass
class IpeOptions:
    stroke_color : str = "black"
    fill_color : str = "white"
    pen : str = "normal"
    mark_size : str = "normal"
    cap : str = None
    background_color: str = "white"
    
@dataclass
class MDOptions:
    width : int = 200
    
class StylefileTagParser(ABC):
    def __init__(self, template, options = IpeOptions(), layout = MDOptions()):
        self.template = template
        self.options = options
        self.layout = layout

    def _render_template(self, name):
        template = get_template(self.template)
        ipe = template.render({
            "name" : name,
            "options" : self.options
        })

        return ipe

    def _make_parsed(self, ipetype, name, ipe):
        return {"type" : ipetype, "name" : name, "ipe" : ipe}

    @abstractmethod
    def applies(self, tag):
        pass

    @abstractmethod
    def parse(self, name, hint):
        pass

class SymbolParser(StylefileTagParser):
    def __init__(self, symbolname, template, options = IpeOptions(), layout = MDOptions()):
        super().__init__(template, options, layout)
        self.symbolname = symbolname

    def applies(self, tag):
        return tag.name == "symbol" and tag["name"].startswith(self.symbolname)

    def _make_parsed(self, name, ipe):
        return super()._make_parsed(self.symbolname, name, ipe)

class MarkParser(SymbolParser):
    TEMPLATE = "mark.jinja2"

    def __init__(self, options = IpeOptions(), layout = MDOptions()):
        super().__init__("mark", MarkParser.TEMPLATE, options, layout)
        
    def parse(self, name):
        ipe = self._render_template(name)
        return self._make_parsed(name, ipe)

class DecorationParser(SymbolParser):
    TEMPLATE = "decoration.jinja2"

    def __init__(self, options = IpeOptions(), layout = MDOptions()):
        super().__init__("decoration", DecorationParser.TEMPLATE, options, layout)
        
    def parse(self, name):
        ipe = self._render_template(name)
        return self._make_parsed(name, ipe)

class ArrowParser(SymbolParser):
    TEMPLATE = "arrow.jinja2"

    def __init__(self, options = IpeOptions(), layout = MDOptions()):
        super().__init__("arrow", ArrowParser.TEMPLATE, options, layout)

    def parse(self, name):
        ipe = self._render_template(name.replace("arrow/", "").replace("(spx)", ""))
        return self._make_parsed(name, ipe)

class PropertyParser(StylefileTagParser):
    def __init__(self, propertyname, template, options = IpeOptions(), layout = MDOptions()):
        super().__init__(template, options, layout)
        self.propertyname = propertyname

    def applies(self, tag):
        return tag.name == self.propertyname

    def _make_parsed(self, name, ipe):
        return super()._make_parsed(self.propertyname, name, ipe)

class DashParser(PropertyParser):
    TEMPLATE = "dashstyle.jinja2"

    def __init__(self, options = IpeOptions(), layout = MDOptions()):
        super().__init__("dashstyle", DashParser.TEMPLATE, options, layout)

    def parse(self, name):
        ipe = self._render_template(name)
        return self._make_parsed(name, ipe)

class ColorParser(PropertyParser):
    TEMPLATE = "color.jinja2"

    def __init__(self, options = IpeOptions(), layout = MDOptions()):
        super().__init__("color", ColorParser.TEMPLATE, options, layout)

    def parse(self, name):
        ipe = self._render_template(name)
        return self._make_parsed(name, ipe)

class TextstyleParser(PropertyParser):
    TEMPLATE = "textstyle.jinja2"

    def __init__(self, options = IpeOptions(), layout = MDOptions()):
        super().__init__("textstyle", TextstyleParser.TEMPLATE, options, layout)

    def parse(self, name):
        ipe = self._render_template(name)
        return self._make_parsed(name, ipe)

@dataclass
class Example:
    name: str
    picture_path: pathlib.Path
    folder: str
    layout: MDOptions = MDOptions()
    
    def set_testing_path(self, svgpath):
        self.picture_path = pathlib.Path(svgpath) / self.picture_path.name

def get_name(ipe_name):
    return ipe_name.replace("/", "")

#TODO: Should be moved to some form of util component
def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])

def process_tag(tag, hints):
    item = None
    for parser_cls in all_subclasses(StylefileTagParser):
        if not inspect.isabstract(parser_cls):
            parser = parser_cls()
            if parser.applies(tag):
                name = tag["name"]
                
                #TODO: Tag and layout hints currently do not work for symbols, fix.
                if hints:
                    tag_hints = hints["tags"].get(tag.name, dict())
                    style_hints = hints["styles"].get(name, dict())
                    hints_dict = dict(tag_hints, **style_hints)
                    parser.options = IpeOptions(**hints_dict)
                    
                item = parser.parse(name)

    return item

def examples_from_stylefile(soup, svgpath, renderfile, folder, hints):
    template = get_template(IPE_TEMPLATE_FILE)
    
    items = []
    for child in soup.ipestyle.children:
        if child != "\n":
            item = process_tag(child, hints)
            if item != None:
                items.append(item)

    template_variables = {
        "stylesheets" : [soup.ipestyle],
        "items" : items
    }

    #TODO: Should make a temporary file instead
    output = template.render(template_variables)
    with open(renderfile, "w") as fp:
        fp.write(output)

    examples = []
    for item in items:
        page = item["name"]
        svgname = get_name(item["name"]) + ".svg"
        svgname = pathlib.Path(svgname.replace(" ", "_"))
        outfile = svgpath / svgname
        subprocess.run(["iperender", "-svg", "-page", page, renderfile, outfile],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT)

        with open(outfile, "r+") as fp:
            figsoup = BeautifulSoup(fp, "xml")
            figsoup.svg["style"] = "background-color:white"
            fp.seek(0)
            fp.write(figsoup.prettify())

        example = Example(page, outfile, folder)
        
        if hints:
            layout_hints = hints["layout"].get(item["type"], dict())
            example.layout = MDOptions(**layout_hints)
            
        examples.append(example)

    return examples