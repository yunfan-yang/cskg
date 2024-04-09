from loguru import logger

from cskg.detectors.detector import AbstractDetector
from cskg.utils.graph_component import GraphComponent


class BaseClassDependsOnSubclassDetector(AbstractDetector):
    def detect(self):
        self.result_collection = self.mongo_db.get_collection(
            "base_class_depends_on_subclass"
        )

        query = """
            MATCH (parent:Class)-[relationship]->(child:Class)
            WHERE NOT type(relationship) = "INHERITS" 
                AND (child)-[:INHERITS]->(parent)
            RETURN parent, child, COLLECT(relationship) AS relationships
        """
        logger.debug(query)

        results, meta = self.neo_db.cypher_query(query)

        logger.debug(results)

        for result in results:
            parent_node, child_node, relationship_node = result

            parent = GraphComponent.from_node(parent_node)
            child = GraphComponent.from_node(child_node)

            self.result_collection.insert_one(
                {
                    "parent": parent,
                    "child": child,
                    "relationships": relationship_node,
                }
            )
