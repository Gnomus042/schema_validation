from rdflib import Graph
import json
from collections import defaultdict

default_schema_path = 'data/schema.jsonld'


class PropertyNames:
    def __init__(self):
        self.class_type = "rdfs:Class"
        self.property_type = "rdf:Property"

        self.id = "@id"
        self.type = "@type"
        self.label = "rdfs:label"
        self.comment = "rdfs:comment"
        self.subClassOf = "rdfs:subClassOf"
        self.domainIncludes = "http://schema.org/domainIncludes"
        self.rangeIncludes = "http://schema.org/rangeIncludes"


property_names = PropertyNames()


class Helper:
    @staticmethod
    def extract_names(source):
        source = [source] if type(source) == dict else source
        return [x[property_names.id] for x in source]

    @staticmethod
    def name_from_id(id):
        sidx = id.rfind('/')
        return id[sidx + 1:]


class Property:
    def __init__(self, source: dict):
        self.id = source[property_names.id]
        self.label = source[property_names.label]
        self.source = source
        self.rangeIncludes = []
        self.domainIncludes = []

    def add_info(self, nodes):
        self.rangeIncludes = self.nodes_for(property_names.rangeIncludes, nodes)
        self.domainIncludes = self.nodes_for(property_names.domainIncludes, nodes)
        for domain in self.domainIncludes:
            domain.properties.append(self)

    def nodes_for(self, name: str, nodes: dict):
        res = []
        if name in self.source:
            for node_id in Helper.extract_names(self.source[name]):
                if node_id not in nodes:
                    nodes[node_id] = Node(
                        {property_names.id: node_id, property_names.label: Helper.name_from_id(node_id)})
                res.append(nodes[node_id])
        return res

    def shex_serialize(self):
        serialized_range = []
        for node in self.rangeIncludes:
            serialized_range.append(f"<#{node.name}>")
        if len(serialized_range) == 1:
            return f"schema:{self.label} {serialized_range[0]} ;"
        else:
            return f"schema:{self.label} ({' OR '.join(serialized_range)}) ;"

    def shacl_serialize(self):
        pass


class Node:
    def __init__(self, source: dict):
        self.id = source[property_names.id]
        if property_names.label in source:
            self.name = source[property_names.label]
        else:
            self.name = self.id
        if property_names.comment in source:
            self.comment = source[property_names.comment]
        self.source = source
        self.properties = []
        self.subclass_of = []
        self.parent_to = []
        self.children_found = False

    def add_info(self, nodes):
        self.subclass_of = []
        if property_names.subClassOf in self.source:
            for node_id in Helper.extract_names(self.source[property_names.subClassOf]):
                if node_id not in nodes:
                    nodes[node_id] = Node(
                        {property_names.id: node_id, property_names.label: Helper.name_from_id(node_id)})
                self.subclass_of.append(nodes[node_id])
        for node in self.subclass_of:
            node.parent_to.append(self)

    def find_children(self):
        for child in self.parent_to:
            self.parent_to.extend(child.find_children())
        self.children_found = True
        self.parent_to = list(set(self.parent_to))
        return self.parent_to


class Generator:
    def __init__(self, schema: dict = None):
        self.graph = dict()
        self.properties = dict()
        self.schema = (schema if schema else self.get_schema_json(default_schema_path))['@graph']
        self.build_graph()

    def build_graph(self):
        for item in self.schema:
            if item[property_names.type] == property_names.class_type:
                node = Node(item)
                self.graph[node.id] = node
            elif item[property_names.type] == property_names.property_type:
                property = Property(item)
                self.properties[property.id] = property
        for node in list(self.graph.values()):
            node.add_info(self.graph)
        for property in list(self.properties.values()):
            property.add_info(self.graph)
        for node in self.graph.values():
            if not node.children_found:
                node.find_children()

    def get_schema_json(self, path):
        return json.loads(open(path).read())

    def print_as_shex(self, node_id):
        node = self.graph[node_id]
        node_name = f"<#{node.name}>"
        subslass_of = f"@<#{node.subclass_of[0].name}> AND" if len(node.subclass_of) > 0 else ""
        children = ' '.join(['schema:' + x.name for x in node.parent_to + [node]])
        properties = '\n\t'.join([x.shex_serialize() for x in node.properties])
        return f"{node_name} {subslass_of} EXTRA a {{ \n\ta [{children}];\n\t{properties}\n}}"


if __name__ == '__main__':
    g = Generator()
    print(g.print_as_shex('http://schema.org/HowTo'))
