import os
import logging
from logging.handlers import RotatingFileHandler

from app import create_app  # this imports app

# create a file handler to store weblogs
os.makedirs("tmp", exist_ok=True)
handler = RotatingFileHandler("tmp/tmp.log", maxBytes=1000000000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s {%(pathname)s:%(lineno)d} - %(message)s"
)
handler.setFormatter(formatter)

app = create_app()
app.logger.setLevel(logging.INFO)
app.logger.addHandler(handler)

# run the application
app.run(debug=True)
