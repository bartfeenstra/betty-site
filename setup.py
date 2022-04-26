"""Integrates the Betty site with Python's setuptools."""

from setuptools import setup, find_packages

SETUP = {
    'name': 'betty-site',
    'license': 'GPLv3',
    'python_requires': '~= 3.9',
    'install_requires': [
        'jinja2 ~= 3.1.1',
        'semver ~= 2.13.0',
    ],
    'extras_require': {
        'development': [
            'autopep8 ~= 1.6.0',
            'flake8 ~= 4.0.1',
        ],
    },
    'packages': find_packages(),
}

if __name__ == '__main__':
    setup(**SETUP)
