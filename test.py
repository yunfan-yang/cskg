import os
from dotenv import load_dotenv

from cskg.driver import Driver

# Load environment variables
load_dotenv()


# NEO4J_REQUESTS_URL = os.environ.get("NEO4J_REQUESTS_URL")
# MONGO_REQUESTS_URL = os.environ.get("MONGO_REQUESTS_URL")

# driver_requests = Driver(
#     "targets/requests",
#     neo4j_url=NEO4J_REQUESTS_URL,
#     mongo_url=MONGO_REQUESTS_URL,
# )
# driver_requests.run(interpret=False, compose=False, detect=True)


# NEO4J_URL_TRANSFORMERS = os.environ.get("NEO4J_URL_TRANSFORMERS")
# MONGO_URL_TRANSFORMERS = os.environ.get("MONGO_URL_TRANSFORMERS")
# driver_transformers = Driver(
#     "targets/transformers",
#     neo4j_url=NEO4J_URL_TRANSFORMERS,
#     mongo_url=MONGO_URL_TRANSFORMERS,
# )
# driver_transformers.run(interpret=False, compose=False, detect=False)


NEO4J_URL_PYTORCH = os.environ.get("NEO4J_URL_PYTORCH")
MONGO_URL_PYTORCH = os.environ.get("MONGO_URL_PYTORCH")
driver_transformers = Driver(
    "targets/pytorch",
    neo4j_url=NEO4J_URL_PYTORCH,
    mongo_url=MONGO_URL_PYTORCH,
)
driver_transformers.run(interpret=False, compose=False, detect=True)
