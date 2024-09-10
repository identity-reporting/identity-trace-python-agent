from setuptools import setup

setup(
    name='identity-trace-python-agent',
    version='1.0.13',
    packages=["identity_trace"],
    description='Tracing agent for python.',
    author='Mamoon Ahmed',
    author_email='engineer.mamoonahmed@gmail.com',
    url='https://github.com/MamoonAhmad/identity-reporting/tree/main/identity-trace-python-agent',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        "jsonpickle",
        "requests"
    ],
)