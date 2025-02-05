import logging

# Create a logger
logger = logging.getLogger("whatsapp_bot")  # Use a unique name
logger.setLevel(logging.INFO)

# File Handler (Logs to app.log)
file_handler = logging.FileHandler("./logs/app.log")
file_handler.setLevel(logging.INFO)

# Console Handler (Logs to terminal)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Define log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Prevent duplicate logs
logger.propagate = False

LOGGER = logger 