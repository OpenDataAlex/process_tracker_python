import logging
import os

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s",
)

console = logging.StreamHandler()
console.setLevel(os.environ.get("log_level", "DEBUG"))

# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s"
)

# set formatter
console.setFormatter(formatter)
