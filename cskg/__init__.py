import time
from loguru import logger

# Initialize logger file
filename = time.strftime("%Y-%m-%d_%H-%M-%S")
logger.add(
    f"logs/{filename}.log",
    filter=lambda record: record["level"].name not in ["DEBUG", "ERROR"],
)
logger.add(
    f"logs/{filename}.debug.log", filter=lambda record: record["level"].name == "DEBUG"
)
logger.add(
    f"logs/{filename}.error.log", filter=lambda record: record["level"].name == "ERROR"
)
