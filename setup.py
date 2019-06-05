import setuptools

from process_tracker import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="processtracker",
    version=__version__,
    author="Alex Meadows",
    author_email="alexmeadows@bluefiredatasolutions.com",
    description="A framework for managing data integration processes and their data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opendataalex/process_tracker_python",
    packages=setuptools.find_packages(),
    test_suite="tests.process_tracker_test_suite",
    install_requires=[
        "boto3 >= 1.9.150",
        "Click >= 7.0",
        "cx-oracle >= 7.1.3",
        "google-compute-engine >= 2.8.13",
        "psycopg2-binary >= 2.8.2",
        "pymysql >= 0.9.3",
        "pymssql >= 2.1.4",
        "python-dateutil >= 2.8.0",
        "snowflake-sqlalchemy >= 1.1.13",
        "sqlalchemy >= 1.3.3",
        "sqlalchemy-utils >= 0.33.11",
    ],
    extras_requires={
        "dev": [
            "black >= 19.3b0",
            'coverage >= "4.0.3',
            "coveralls >= 1.7.0",
            "moto >= 1.3.8",
            "python-coveralls >= 2.9.1",
        ]
    },
    entry_points={"console_scripts": ["process_tracker=process_tracker.cli:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Software Development",
    ],
)
