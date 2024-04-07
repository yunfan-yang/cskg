from abc import ABC
from collections import defaultdict
from typing import Iterable
from neo4j.exceptions import ClientError
from loguru import logger
from neo4j.graph import Path
from tqdm import tqdm

from cskg.detectors.detector import AbstractDetector
from cskg.utils.graph_component import GraphComponent
from cskg.utils.relationship import TakesRel


class DataClumpsDetector(AbstractDetector):
    label = "DataClumps"

    def detect(self):
        self.root = FpTreeNode(
            class_qualified_name="<<Root>>",
            param_name="root",
            level=0,
            support_count=0,
        )
        self.result_collection = self.mongo_db.get_collection("data_clumps")

        # Create root node of FP Growth tree
        self.clear_everything()
        self.create_index()
        self.create_fp_tree_root()

        # Build FP-growth tree
        self.build_fp_growth_tree()
        self.build_conditional_fp_tree()

    def build_fp_growth_tree(self):
        query = f"""
            MATCH (c:Class)<-[t:TAKES]-(f:Function)
            WITH c, t.param_name AS param_name, COUNT(DISTINCT f) AS frequency
            WHERE frequency >= 2
            RETURN c, param_name, frequency
            ORDER BY frequency DESC
        """
        results, meta = self.neo_db.cypher_query(query)
        freq_table = defaultdict(int)
        for result in results:
            c, param_name, frequency = result
            freq_table[c["qualified_name"], param_name] = frequency

        query = f"""
            MATCH (f:Function)-[t:TAKES]->(c:Class)
            WITH f, COLLECT(t) AS ts, COUNT(t) AS ts_count
            WHERE ts_count >= 3
            RETURN f, ts
        """
        results, meta = self.neo_db.cypher_query(query)
        for result in tqdm(results, desc="Building FP Growth Tree", unit="functions"):
            f, ts = result
            takes_rels: list[TakesRel] = [GraphComponent.from_neo_node(t) for t in ts]
            takes_rels = [
                t
                for t in takes_rels
                if freq_table[t.to_qualified_name, t.param_name] >= 2
            ]
            takes_rels.sort(
                key=lambda t: freq_table[t.to_qualified_name, t.param_name],
                reverse=True,
            )

            transaction = Transaction()
            transaction.append(self.root)

            for index, takes_rel in enumerate(takes_rels):
                item = FpTreeNode(
                    param_name=takes_rel.param_name,
                    class_qualified_name=takes_rel.to_qualified_name,
                    level=index + 1,
                )
                transaction.append(item)

            # Insert transaction into FP Growth tree
            self.insert_transaction(transaction, FpTreeNode.get_labels())

    def build_conditional_fp_tree(self):
        # Find all distinct items
        query = f"""
            MATCH (n:{FpTreeNode.label})
            WHERE n.class_qualified_name <> "{self.root.class_qualified_name}"
                AND n.param_name <> "{self.root.param_name}"
            WITH DISTINCT {{
                class_qualified_name: n.class_qualified_name,
                param_name: n.param_name
            }} AS n
            RETURN n
        """
        logger.debug(query)
        results, meta = self.neo_db.cypher_query(query)

        bar = tqdm(results, desc="Building Conditional FP Tree", unit="nodes")
        for index, (n,) in enumerate(bar):
            # Create Conditional FP Tree Node
            fp_item = FpTreeNode.from_neo_node(n)

            query = f"""
                MATCH path =
                    (root:{FpTreeNode.label} {{
                        node_id: "{self.root.node_id}"
                    }})-[:LINKS*]->(end:{FpTreeNode.label} {{
                        class_qualified_name: "{fp_item.class_qualified_name}",
                        param_name: "{fp_item.param_name}"
                    }})
                RETURN path, end
            """
            paths, meta = self.neo_db.cypher_query(query)
            for path, end in tqdm(paths, desc="Inserting paths", unit="paths"):
                # Assign type
                path: Path
                path_nodes = list(path.nodes)

                # Convert cfp_node
                cfp_end = ConditionalFpTreeNode.from_neo_node(end)

                # Insert path into Conditional Pattern Base
                transaction = Transaction()
                for node in path_nodes:
                    cfp_node = ConditionalFpTreeNode.from_neo_node(node)
                    logger.debug(cfp_node.node_id)
                    cfp_node.level = index + 1
                    cfp_node.support_count = min(
                        cfp_node.support_count,
                        cfp_end.support_count,
                    )
                    transaction.append(cfp_node)

                logger.debug(transaction)

                # Insert transaction into Conditional Pattern Base
                self.insert_transaction(transaction, ConditionalFpTreeNode.get_labels())

            # Query for CFP Tree
            level = index + 1
            query = f"""
                MATCH path = 
                    (root:{ConditionalFpTreeNode.label} {{
                        level: {level}
                    }})-[:LINKS*]->(end:{ConditionalFpTreeNode.label} {{
                        level: {level}
                    }})
                RETURN path, end
            """
            paths, meta = self.neo_db.cypher_query(query)
            patterns = []
            for path, end in paths:
                nodes = list(
                    filter(lambda node: node["support_count"] >= 3, path.nodes[1:-1])
                )
                if len(nodes) > 0:
                    patterns.append(nodes)

            for pattern in patterns:
                logger.debug(pattern)
                self.result_collection.insert_one(
                    {
                        "pattern": pattern,
                        "support_count": min(
                            map(lambda node: node["support_count"], pattern)
                        ),
                    }
                )

            # Clear CFP Tree
            query = f"""
                MATCH (n:{ConditionalFpTreeNode.label})
                WHERE n.level = {level}
                DETACH DELETE n
            """
            logger.debug(query)
            self.neo_db.cypher_query(query)

    def insert_transaction(
        self, transaction: "Transaction", labels: Iterable[str] = None
    ):
        if not labels:
            labels = [self.label]

        labels_str = "".join(map(lambda label: f":{label}", labels))

        query = f"""
            UNWIND $items AS item
            MERGE (parent:{self.label} {{
                node_id: item.parent.node_id
            }})
            MERGE (parent)-[:LINKS]->(child{labels_str} {{
                class_qualified_name: item.child.class_qualified_name,
                param_name: item.child.param_name,
                level: item.child.level,
                node_id: item.child.node_id
            }})
            ON CREATE
                SET child += item.child
            ON MATCH
                SET child.support_count = child.support_count + 1
        """
        logger.debug(query)

        with self.neo_db.transaction:
            items = list(
                map(
                    lambda item: {"parent": item[0], "child": item[1]},
                    zip(transaction[:-1], transaction[1:]),
                )
            )
            self.neo_db.cypher_query(query, {"items": items})

    def create_fp_tree_root(self):
        labels = "".join(map(lambda label: f":{label}", self.root.labels))
        query = f"""
            MERGE (root{labels} {{node_id: $root.node_id}})
            ON CREATE
                SET root += $root
            ON MATCH
                SET root += $root
            RETURN root
        """
        logger.debug(query)
        self.neo_db.cypher_query(query, {"root": self.root})

    def create_index(self):
        query = f"""
            CREATE INDEX {self.label}_class_qname_param_name_level 
            FOR (n:{self.label}) 
            ON (n.class_qualified_name, n.param_name, n.level)
        """
        try:
            self.neo_db.cypher_query(query)
        except ClientError as e:
            logger.error(e)

        query = f"""
            CREATE INDEX {self.label}_node_id
            FOR (n:{self.label})
            ON (n.node_id)
        """
        try:
            self.neo_db.cypher_query(query)
        except ClientError as e:
            logger.error(e)

    def clear_everything(self):
        query = f"""
            MATCH (n: {self.label})
            RETURN COUNT(n) AS count
        """
        results, meta = self.neo_db.cypher_query(query)
        count = results[0][0]

        if count == 0:
            return

        query = f"""
            MATCH (n: {self.label})
            WITH n
            LIMIT 10000
            DETACH DELETE n
        """
        logger.debug(query)
        for _ in tqdm(range(0, count, 10000), desc="Clearing"):
            self.neo_db.cypher_query(query)


class FpTreeNode(GraphComponent):
    type = "fp_tree_node"
    label = "FpTreeNode"
    extra_labels = (DataClumpsDetector.label,)

    def __init__(
        self,
        param_name: str,
        class_qualified_name: str,
        level: int = 1,
        support_count: int = 1,
        **kwargs,
    ):
        self.param_name: str
        self.class_qualified_name: str
        self.level: int
        self.support_count: int
        super().__init__(
            param_name=param_name,
            class_qualified_name=class_qualified_name,
            level=level,
            support_count=support_count,
            **kwargs,
        )
        if not hasattr(self, "node_id"):
            self.node_id = f"{self.label}_{self.class_qualified_name}_{self.param_name}_{self.level}"


class Transaction(list[FpTreeNode]): ...


class ConditionalFpTreeNode(FpTreeNode):
    type = "conditional_fp_tree_node"
    label = "ConditionalFpTreeNode"
