import time
import os
import sys
import importlib
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


# Import all modules
def import_classes_from_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]  # Remove .py extension
            module_path = os.path.join(directory, filename)

            # Create module spec and load the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)


import_classes_from_directory("cskg/detectors")
