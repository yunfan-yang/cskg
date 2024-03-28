from loguru import logger

from cskg.detectors.detector import AbstractDetector
from cskg.utils.entity import ClassEntity


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

        results, meta = self.neo_db.cypher_query(query)

        logger.debug(results)

        for result in results:
            ents = self.response_to_ent(result)
            logger.debug(ents)
