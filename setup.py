from setuptools import setup

setup(
    name='ipecol',
    version='0.1.0',
    py_modules=['ipecol'],
    install_requires=[
        'Click',
        'jinja2',
        'bs4',
        'lxml'
    ],
    entry_points={
        'console_scripts': [
            'ipecol = ipecol:cli',
        ],
    },
)