import os
from dotenv import load_dotenv

from driver import Driver

# Load environment variables
load_dotenv()

NEO4J_URL = os.environ.get("NEO4J_URL")
MONGO_URL = os.environ.get("MONGO_URL")

configs = {
    "NEO4J_URL": NEO4J_URL,
    "MONGO_URL": MONGO_URL,
}
driver = Driver("targets/transformers", configs)
driver.run()
