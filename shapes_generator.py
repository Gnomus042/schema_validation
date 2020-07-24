import json
from enum import Enum


class SchemaType(Enum):
    class_type = "rdfs:Class"
    property_type = "rdf:Property"


class SchemaProperty(Enum):
    id = "@id"
    type = "@type"
    label = "rdfs:label"
    comment = "rdfs:comment"
    subClassOf = "rdfs:subClassOf"
    domainIncludes = "http://schema.org/domainIncludes"
    rangeIncludes = "http://schema.org/rangeIncludes"


class Helper:
    @staticmethod
    def extract_options(source):
        source = [source] if type(source) == dict else source
        return [x[SchemaProperty.id.value] for x in source]

    @staticmethod
    def label_from_id(id):
        slash_idx = id.rfind('/')
        return id[slash_idx + 1:]


class Property:
    def __init__(self, source: dict):
        self.id = source[SchemaProperty.id.value]
        self.label = source[SchemaProperty.label.value]
        self.source = source
        self.rangeIncludes = []
        self.domainIncludes = []

    # fills the property object with all related node objects
    def add_info(self, nodes):
        self.rangeIncludes = self.option_nodes_for_prop(SchemaProperty.rangeIncludes.value, nodes)
        self.domainIncludes = self.option_nodes_for_prop(SchemaProperty.domainIncludes.value, nodes)
        for domain in self.domainIncludes:
            domain.properties.append(self)

    # find all possible nodes that can be in rangeIncludes or domainIncludes for this property
    def option_nodes_for_prop(self, name: str, nodes: dict):
        res_nodes = []
        if name in self.source:
            for node_id in Helper.extract_options(self.source[name]):
                # add new node to graph, if one discovered
                if node_id not in nodes:
                    nodes[node_id] = Node({SchemaProperty.id.value: node_id,
                                           SchemaProperty.label.value: Helper.label_from_id(node_id)})
                res_nodes.append(nodes[node_id])
        return res_nodes

    def to_shex(self):
        values_range = [f"@<#{node.label}>" for node in self.rangeIncludes]
        values_range_str = values_range[0] if len(values_range) == 1 else f"({' OR '.join(values_range)})"
        return f"schema:{self.label} {values_range_str} ;"

    def to_shacl(self, base_ident):
        def indent(x):
            return '\t' * (base_ident + x)

        values_range = [f"sh:node :{node.label}" for node in self.rangeIncludes]
        if len(values_range) == 1:
            values_range_str = f"{values_range[0]};"
        else:
            values_range = '\n'.join([f"{indent(2)}{x}" for x in values_range])
            values_range_str = f"sh:or (\n{values_range}\n{indent(1)});"
        return f"{indent(0)}sh:property [\n{indent(1)}sh:path schema:{self.label};\n{indent(1)}{values_range_str}\n{indent(0)}]"


class Node:
    def __init__(self, source: dict):
        self.id = source[SchemaProperty.id.value]
        if SchemaProperty.label.value in source:
            self.label = source[SchemaProperty.label.value]
        else:
            self.label = Helper.label_from_id(self.id)
        if SchemaProperty.comment.value in source:
            self.comment = source[SchemaProperty.comment.value]
        self.source = source
        self.properties = []
        self.subclass_of = []
        self.parent_to = []
        self.children_found = False

    # fills the property object with all related node objects
    def add_info(self, nodes):
        self.subclass_of = []
        if SchemaProperty.subClassOf.value in self.source:
            for node_id in Helper.extract_options(self.source[SchemaProperty.subClassOf.value]):
                if node_id not in nodes:
                    nodes[node_id] = Node({SchemaProperty.id.value: node_id,
                                           SchemaProperty.label.value: Helper.label_from_id(node_id)})
                self.subclass_of.append(nodes[node_id])
        for node in self.subclass_of:
            node.parent_to.append(self)

    # finds all extending shapes using DFS
    def find_children(self):
        for child in self.parent_to:
            self.parent_to.extend(child.find_children())
        self.children_found = True
        self.parent_to = list(set(self.parent_to))
        return self.parent_to


class ShapesGenerator:
    def __init__(self, schema: dict):
        self.graph = dict()
        self.properties = dict()
        try:
            self.schema = schema['@graph']
        except Exception as ex:
            print("Can't use this schema file. \nDescription:", str(ex))
        self.build_graph()

    def build_graph(self):
        # Stage 1: extract nodes and properties from the source file
        for item in self.schema:
            if item[SchemaProperty.type.value] == SchemaType.class_type.value:
                node = Node(item)
                self.graph[node.id] = node
            elif item[SchemaProperty.type.value] == SchemaType.property_type.value:
                property = Property(item)
                self.properties[property.id] = property

        # Stage 2.1: fill nodes objects with related properties and nodes objects
        for node in list(self.graph.values()):
            node.add_info(self.graph)

        # Stage 2.2: fill properties objects with related nodes objects
        for property in list(self.properties.values()):
            property.add_info(self.graph)

        # Stage 3: find all extending nodes for each node
        for node in self.graph.values():
            if not node.children_found:
                node.find_children()

    def get_schema_json(self, path):
        return json.loads(open(path).read())

    def to_shex(self, node_id):
        node = self.graph[node_id]
        node_name = f"<#{node.label}>"
        subclass_of = f"@<#{node.subclass_of[0].label}> AND" if len(node.subclass_of) > 0 else ""
        children = ' '.join(['schema:' + x.label for x in node.parent_to + [node]])
        properties = ''.join(['\n\t'+x.to_shex() for x in sorted(node.properties, key=lambda x: x.label)])
        return f"{node_name} {subclass_of} EXTRA a {{ \n\ta [{children}];{properties}\n}}"

    def to_shacl(self, node_id):
        node = self.graph[node_id]

        def indent(x):
            return "\t" * x
        extension = ""
        if len(node.subclass_of) > 0:
            extension = f"\n\tsh:node :{node.subclass_of[0].label};"
        props = f';\n'.join([x.to_shacl(1) for x in sorted(node.properties, key=lambda x: x.label)])
        return f":{node.label} a sh:NodeShape;\n\tsh:targetClass schema:{node.label};{extension}\n{props}."
