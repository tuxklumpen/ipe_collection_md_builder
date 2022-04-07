from setuptools import setup

setup(
    name='ipecol',
    version='0.1.0',
    py_modules=['ipecol'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'ipecol = ipecol:cli',
        ],
    },
)