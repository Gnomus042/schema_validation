from pyshex import ShExEvaluator
from rdflib import Graph, plugin
from rdflib.serializer import Serializer
import json

if __name__ == '__main__':
    shex = open('data/recipe_shex.shex').read()
    jsonld = open('data/recipe_jsonld.json').read()
    context = json.loads(open('data/context.json').read())

    g = Graph().parse(data=jsonld, context=context, format='json-ld')
    print(g.serialize(format='json-ld', indent=4).decode('utf-8'))

    evaluator = ShExEvaluator(schema=shex, start="http://schema.org/shex#Recipe")
    results = evaluator.evaluate(g, focus="http://example.org/recipe", rdf_format="json-ld")
    for r in results:
        if not r.result:
            print(r.reason)
            break
    else:
        print("Success")
