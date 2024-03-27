from loguru import logger
from cskg.detectors.detector import AbstractDetector


class SpeculativeGeneralityDetector(AbstractDetector):
    def detect(self):
        query = """
            MATCH (a:Class {is_abstract: true})
            OPTIONAL MATCH (a)<-[:INHERITS]-(inheriting_class)
            WITH a,
                COUNT(inheriting_class) AS inherits_count
            WHERE inherits_count <= 1
            RETURN a
        """
        logger.debug(query)

        r = self.neo_db.cypher_query(query)
        logger.debug(list(r))
