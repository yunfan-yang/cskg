import os
from dotenv import load_dotenv

from cskg.driver import Driver

# Load environment variables
load_dotenv()

NEO4J_URL = os.environ.get("NEO4J_URL")
MONGO_URL = os.environ.get("MONGO_URL")

NEO4J_REQUESTS_URL = os.environ.get("NEO4J_REQUESTS_URL")
MONGO_REQUESTS_URL = os.environ.get("MONGO_REQUESTS_URL")

driver = Driver("targets/transformers", neo4j_url=NEO4J_URL, mongo_url=MONGO_URL)
driver.run(interpret=False, compose=False, detect=True)

driver_requests = Driver(
    "targets/requests",
    neo4j_url=NEO4J_REQUESTS_URL,
    mongo_url=MONGO_REQUESTS_URL,
)
driver_requests.run(interpret=True, compose=True, detect=True)
