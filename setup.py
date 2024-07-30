from setuptools import setup, find_packages
import os

# Read the contents of the README file
with open(os.path.join(os.path.dirname(__file__), 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    author='Muhammad Wisal',
    author_email='wisal@lowerated.com',
    description='Lowerated is an opensource library that allows you to rate any item in a statistically accurate way',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://lowerated.com/products/',
    name='lowerated',
    version='0.2.6',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'python-dotenv',
        'websockets',
        'fastapi'
    ],
    extras_require={
        'openai': ['openai'],
    },
    dependency_links=[],
)
