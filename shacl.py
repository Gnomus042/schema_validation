import json

from pyshacl import validate
from rdflib import Graph


def fill_blanks(pre_shex):
    substs = json.loads(open('data/substs.json').read())
    res = pre_shex
    for s in substs:
        res = res.replace(f"<%{s}%>", substs[s])
        print(res)
    return res


if __name__ == '__main__':
    jsonld = open('data/recipe_jsonld.json').read()
    shacl = fill_blanks(open('data/shacl.txt').read())
    context = json.loads(open('data/context.json').read())

    g = Graph().parse(data=jsonld, context=context, format='json-ld')
    print(g.serialize(format='json-ld', indent=4).decode('utf-8'))

    gsh = Graph().parse(data=shacl, format='turtle')
    print(gsh.serialize(format='turtle', indent=4).decode('utf-8'))

    res = validate(g, shacl_graph=gsh)
    conforms, graph, string = res
    print("Confroms:", conforms)
    print("String:", string)
