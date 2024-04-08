from loguru import logger

from cskg.detectors.detector import AbstractDetector
from cskg.utils.graph_component import GraphComponent


class SpeculativeGeneralityDetector(AbstractDetector):
    def detect(self):
        self.result_collection = self.mongo_db.get_collection("speculative_generality")

        query = """
            MATCH (cls:Class {is_abstract: true})
            OPTIONAL MATCH (cls)<-[:INHERITS]-(inheriting_class)
            WITH cls, 
                COUNT(inheriting_class) AS inherits_count
            WHERE inherits_count <= 1
            RETURN cls, inherits_count
        """
        logger.debug(query)

        results, meta = self.neo_db.cypher_query(query)

        logger.debug(results)

        for result in results:
            cls_node, inherits_count = result
            ent = GraphComponent.from_neo_node(cls_node)
            self.result_collection.insert_one(
                {
                    "entity": ent,
                    "inherits_count": inherits_count,
                }
            )
