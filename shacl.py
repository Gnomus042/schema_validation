import json
import re

from pyshacl import validate
from rdflib import Graph


def fill_blanks(pre_shex):
    substs = json.loads(open('data/substs.json').read())
    changed = True
    res = pre_shex
    while changed:
        match = re.search('<%(.*?)%>', res)
        if bool(match):
            s = match.group(1)
            res = res.replace(f"<%{s}%>", substs[s])
        else:
            changed = False
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
