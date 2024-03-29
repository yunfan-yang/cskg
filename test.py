import os
from dotenv import load_dotenv

from cskg.driver import Driver

# Load environment variables
load_dotenv()

NEO4J_URL = os.environ.get("NEO4J_URL")
MONGO_URL = os.environ.get("MONGO_URL")

driver = Driver("targets/transformers", neo4j_url=NEO4J_URL, mongo_url=MONGO_URL)
driver.run(interpret=False, compose=True, detect=True)
