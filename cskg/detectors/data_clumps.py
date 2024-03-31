from loguru import logger

from cskg.detectors.detector import AbstractDetector
from cskg.utils.entity import ClassEntity, Entity, FunctionEntity
from cskg.utils.graph_component import GraphComponent
from cskg.utils.relationship import TakesRel


class Item(GraphComponent):
    type = "item"
    label = "Item"
    extra_labels = ("DataClumps",)

    def __init__(
        self,
        param_name: str,
        class_qualified_name: str,
        level: int = 1,
        frequency: int = 1,
        **kwargs,
    ):
        self.param_name: str
        self.class_qualified_name: str
        self.level: int
        self.frequency: int

        super().__init__(
            param_name=param_name,
            class_qualified_name=class_qualified_name,
            level=level,
            frequency=frequency,
            **kwargs,
        )


class Transaction(list[Item]): ...


class DataClumpsDetector(AbstractDetector):
    def detect(self):
        # Create root node of FP Growth tree
        self.clear_fp_growth_tree()
        self.create_root()

        # Frequency Pattern Growth algorithm
        query = """
            // Step 1: Calculate class frequencies considering both class qualified_name and TAKES param_name
            MATCH (c:Class)<-[t:TAKES]-(f:Function)
            WITH c, t.param_name AS param_name, COUNT(DISTINCT f) AS functions_count
            WHERE functions_count >= 3
            WITH c, param_name, COUNT(*) AS freq
            ORDER BY freq DESC

            // Store frequencies in a way that can be used in later matching, including both qualified_name and param_name
            WITH COLLECT({class: c, param_name: param_name, freq: freq}) AS classes_with_freqs

            // Step 2: Match Functions and their Classes, bringing in frequency for sorting
            MATCH (f:Function)-[t:TAKES]->(c:Class)
            WITH f, t, c, classes_with_freqs,
                [x IN classes_with_freqs WHERE x.class = c AND x.param_name = t.param_name][0].freq AS freq
            ORDER BY freq DESC

            // Step 3: Collect relationships, ensuring classes are sorted by their frequency
            WITH f, COLLECT(t) AS ts

            RETURN f, ts
        """

        results, meta = self.neo_db.cypher_query(query)

        for result in results:
            f, ts = result

            takes_rels: list[TakesRel] = [GraphComponent.from_neo_node(t) for t in ts]

            transaction = Transaction()
            for takes_rel in takes_rels:
                item = Item(
                    param_name=takes_rel.param_name,
                    class_qualified_name=takes_rel.to_qualified_name,
                )
                transaction.append(item)

            # Insert transactions into FP Growth tree
            self.insert_transaction(transaction)

    def insert_transaction(self, transaction: Transaction):
        # Insert transactions into FP Growth tree
        prev_item = self.root

        for item in transaction:
            item.level = prev_item.level + 1

            logger.debug(prev_item)
            logger.debug(item)

            labels = "".join(map(lambda label: f":{label}", item.labels))
            query = f"""
                MATCH (parent{labels} {{
                    class_qualified_name: "{prev_item.class_qualified_name}", 
                    param_name: "{prev_item.param_name}",
                    level: {prev_item.level}
                }})
                MERGE (parent)-[:LINKS]->(child{labels} {{
                    class_qualified_name: "{item.class_qualified_name}", 
                    param_name: "{item.param_name}",
                    level: {item.level}
                }})
                ON CREATE
                    SET child += $child_item
                ON MATCH
                    SET child.frequency = child.frequency + 1
            """
            logger.debug(query)
            self.neo_db.cypher_query(query, {"child_item": item})
            prev_item = item

    def create_root(self):
        root = Item(class_qualified_name="Root", param_name="root", level=0)
        labels = "".join(map(lambda label: f":{label}", root.labels))
        query = f"""
            CREATE (root{labels} $root)
            RETURN root
        """
        self.neo_db.cypher_query(query, {"root": root})
        self.root = root

    def clear_fp_growth_tree(self):
        query = """
            MATCH (n:DataClumps)
            DETACH DELETE n
        """
        self.neo_db.cypher_query(query)
        logger.debug("Cleared FP Growth tree")
