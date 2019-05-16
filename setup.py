import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="processtracker",
    version="0.0.1",
    author="Alex Meadows",
    author_email="alexmeadows@bluefiredatasolutions.com",
    description="A framework for managing data integration processes and their data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opendataalex/process_tracker_python",
    packages=setuptools.find_packages(),
    test_suite='tests.process_tracker_test_suite',
    install_requires=[
        'sqlalchemy >= 1.3.3',
        'sqlalchemy-utils >= 0.33.11',
        'python-dateutil >= 2.8.0',
        'psycopg2-binary >= 2.8.2'
    ],
    extras_requires={
        'dev': [
            'coverage >= "4.0.3',
            'python-coveralls >= 2.9.1',
            'coveralls >= 1.7.0',
            'twine >= 1.13.0'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Software Development"
    ],
)