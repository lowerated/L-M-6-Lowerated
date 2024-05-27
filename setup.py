from setuptools import setup, find_packages

setup(
    author='Muhammad Wisal',
    author_email='wisal@lowerated.com',
    description='Lowerated is an opensource library that allows you to Rate any item in a statistically accurate way',
    long_description="If you plan on rating something based on some textual reviews avaialable or any information that criticises the thing"
                     "Lowerated's rating algorithm will allow you to get a statistically accurate and true rating of that product or item.",
    url='http://lowerated.com/products/',
    name='lowerated',
    version='0.1.0',
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
