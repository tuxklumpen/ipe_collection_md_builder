import jinja2
import os

template_loader = jinja2.PackageLoader(package_name = "ipecol", package_path = "templates/")
template_env = jinja2.Environment(loader = template_loader)

def get_template(path):
    template = template_env.get_template(path)
    return template

