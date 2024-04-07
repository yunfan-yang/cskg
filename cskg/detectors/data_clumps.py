from abc import ABC
from collections import defaultdict
import math
from time import sleep
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
            support_count=0,
        )
        self.result_collection = self.mongo_db.get_collection("data_clumps")
        self.result_collection.delete_many({})
        self.freq_table = defaultdict(int)

        # Create root node of FP Growth tree
        self.clear_conditional_fp_nodes()
        # self.clear_everything()
        # self.create_index()
        # self.create_fp_tree_root()

        # Build FP-growth tree
        self.get_frequency_table()
        # self.build_fp_growth_tree()
        self.build_conditional_fp_tree()

    def get_frequency_table(self):
        query = f"""
            MATCH (c:Class)<-[t:TAKES]-(f:Function)
            WITH c, t.param_name AS param_name, COUNT(DISTINCT f) AS frequency
            WHERE frequency >= 2
            RETURN c, param_name, frequency
            ORDER BY frequency DESC
        """
        results, meta = self.neo_db.cypher_query(query)
        for result in results:
            c, param_name, frequency = result
            self.freq_table[c["qualified_name"], param_name] = frequency

    def build_fp_growth_tree(self):
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
                if self.freq_table[t.to_qualified_name, t.param_name] >= 2
            ]
            takes_rels.sort(
                key=lambda t: self.freq_table[t.to_qualified_name, t.param_name],
                reverse=True,
            )

            transaction = Transaction()
            transaction.append(self.root)

            for takes_rel in takes_rels:
                item = FpTreeNode(
                    param_name=takes_rel.param_name,
                    class_qualified_name=takes_rel.to_qualified_name,
                )
                transaction.append(item)

            # Insert transaction into FP Growth tree
            self.insert_transaction(transaction, FpTreeNode.get_labels())

    def build_conditional_fp_tree(self):
        bar = tqdm(
            self.freq_table.keys(),
            desc="Building Conditional FP Tree",
            unit="nodes",
        )
        for class_qualified_name, param_name in bar:
            # Create conditional FP tree
            query = f"""
                MATCH path = (root:{FpTreeNode.label} {{
                    node_id: "{self.root.node_id}"
                }})-[:LINKS*]->(end:{FpTreeNode.label} {{
                    class_qualified_name: "{class_qualified_name}",
                    param_name: "{param_name}"
                }})
                WHERE end.support_count >= 2 AND length(path) >= 3
                WITH collect(path) AS paths
                CALL apoc.refactor.cloneSubgraphFromPaths(paths)
                YIELD input, output, error
                WITH collect(output) AS cloned_entities
                UNWIND cloned_entities AS entity
                WITH entity
                CALL apoc.create.addLabels(entity, ["{ConditionalFpTreeNode.label}"])
                YIELD node
                RETURN node
            """
            logger.debug(query)
            results, meta = self.neo_db.cypher_query(query)

            # Propagate correct support counts
            query = f"""
                MATCH (child:{ConditionalFpTreeNode.label})<-[:LINKS*]-(parent:{ConditionalFpTreeNode.label})
                WHERE NOT (child)-[]->()
                WITH parent, SUM(child.support_count) AS support_count
                SET parent.support_count = support_count
            """
            logger.debug(query)
            self.neo_db.cypher_query(query)

            if len(results) > 100:
                sleep(5)

            # Query for frequent itemsets
            query = f"""
                MATCH path = (root:{ConditionalFpTreeNode.label})-[:LINKS*]->(end:{ConditionalFpTreeNode.label})
                WHERE NOT (end)-[]->()
                RETURN path
            """
            paths, _ = self.neo_db.cypher_query(query)
            for (path,) in paths:
                path: Path
                itemset = [(class_qualified_name, param_name)]
                frequency = math.inf

                nodes = list(path.nodes)
                interim_nodes = nodes[1:-1]
                for node in interim_nodes:
                    cfp_node = ConditionalFpTreeNode.from_neo_node(node)
                    itemset.append((cfp_node.class_qualified_name, cfp_node.param_name))
                    frequency = min(frequency, cfp_node.support_count)

                if len(interim_nodes) > 1:
                    self.result_collection.insert_one(
                        {"itemset": itemset, "support_count": frequency}
                    )

            # Clear CFP Tree
            self.clear_conditional_fp_nodes()

    def insert_transaction(
        self, transaction: "Transaction", labels: Iterable[str] = None
    ):
        if not labels:
            labels = [self.label]

        labels_str = "".join(map(lambda label: f":{label}", labels))

        rels = []
        for parent, child in zip(transaction[:-1], transaction[1:]):
            child.node_id = f"{parent.node_id}_{child.node_id}"
            rels.append(
                {"parent_node_id": parent.node_id, "child_node_id": child.node_id}
            )

        # Create nodes
        query = f"""
            UNWIND $items AS item
            MERGE (node{labels_str} {{
                node_id: item.node_id
            }})
            ON CREATE
                SET node += item
            ON MATCH
                SET node.support_count = node.support_count + 1
        """
        self.neo_db.cypher_query(query, {"items": transaction})

        # Create relationships
        query = f"""
            UNWIND $rels AS rel
            MATCH (parent:{self.label} {{
                node_id: rel.parent_node_id
            }}), (child:{self.label} {{
                node_id: rel.child_node_id
            }})
            MERGE (parent)-[:LINKS]->(child)
        """
        self.neo_db.cypher_query(query, {"rels": rels})

    def create_fp_tree_root(self):
        labels = "".join(map(lambda label: f":{label}", self.root.labels))
        query = f"""
            MERGE (root:Root{labels} {{node_id: $root.node_id}})
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
            CREATE INDEX {self.label}_class_qname_param_name
            FOR (n:{self.label})
            ON (n.class_qualified_name, n.param_name)
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
            CALL {{ WITH n DETACH DELETE n }}
            IN TRANSACTIONS OF 5000 rows
        """
        logger.debug(query)
        self.neo_db.cypher_query(query)

        # Drop indexes and constraints
        query = f"""
            CALL apoc.schema.assert({{}}, {{}})
        """
        self.neo_db.cypher_query(query)

    def clear_conditional_fp_nodes(self):
        query = f"""
            MATCH (n: {ConditionalFpTreeNode.label})
            DETACH DELETE n
        """
        self.neo_db.cypher_query(query)


class FpTreeNode(GraphComponent):
    type = "fp_tree_node"
    label = "FpTreeNode"
    extra_labels = (DataClumpsDetector.label,)

    def __init__(
        self,
        param_name: str,
        class_qualified_name: str,
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
            support_count=support_count,
            **kwargs,
        )
        self.node_id = f"{self.type}_{self.class_qualified_name}_{self.param_name}"


class Transaction(list[FpTreeNode]): ...


class ConditionalFpTreeNode(FpTreeNode):
    type = "conditional_fp_tree_node"
    label = "ConditionalFpTreeNode"
