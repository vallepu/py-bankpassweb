from setuptools import setup, find_packages
setup(
    name = "py-bankpassweb",
    version = "0.1",
    packages = find_packages(),
    exclude_package_data = { '': ['*/local_*.py',]},

    author = "Emanuele Pucciarelli",
    author_email = "ep@acm.org",
    description = "A Python interface to the BankPass Web e-commerce system",
    keywords = "bankpass",
    url = "http://code.google.com/p/py-bankpassweb",
    license = "GPL",

)
