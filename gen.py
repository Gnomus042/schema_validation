from rdflib import Graph
import json
from collections import defaultdict


def get_schema_json():
    return json.loads(open('data/schema.jsonld').read())

def add_property(model, domain, property_name):
    if type(domain) == dict:
        domain = domain["@id"]
    last_bslach = domain.rfind('/')
    domain = domain[last_bslach + 1:]
    model[domain].append(property_name)

def build_model(schema=None):
    if not schema:
        schema = get_schema_json()['@graph']
    model = defaultdict(list)
    # extract properties
    domain_includes = 'http://schema.org/domainIncludes'
    for el in schema:
        if '@type' in el and el['@type'] == "rdf:Property" and domain_includes in el:
            property_name = el['rdfs:label']
            if type(el[domain_includes]) == dict:
                add_property(model, el[domain_includes], property_name)
            else:
                for domain in el[domain_includes]:
                    add_property(model, domain, property_name)
    return model


def print_properties(domain, model=None):
    if not model:
        model = build_model()
    for property_name in model[domain]:
        print(property_name)
