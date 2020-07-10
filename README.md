# schema_validation
**Exploring SHACL and ShEx**

Contains a module ```shapes_generator```, which can be used for automatic ShEx and SHACL shape skeleton generation from the schema json-ld file. 
Generated shape skeletons contain all properties, ranges of possible values for each property and all "parent" shapes, which the target shape extends. 
Other features like min and max counts, severity, messages and etc. should be added manually for now.

## ShEx example

```python
from schema_validation.shapes_generator import ShapesGenerator


schema = json.loads('path_to_schema.json').read())
gen = ShapesGenerator(schema=schema)
print(gen.to_shex('http://schema.org/HowTo'))
```
**Result:**
```
<#HowTo> @<#CreativeWork> AND EXTRA a { 
	a [schema:Recipe schema:HowTo];
	schema:step (<#HowToStep> OR <#Text> OR <#CreativeWork> OR <#HowToSection>) ;
	schema:steps (<#CreativeWork> OR <#ItemList> OR <#Text>) ;
	schema:supply (<#HowToSupply> OR <#Text>) ;
	schema:tool (<#HowToTool> OR <#Text>) ;
	schema:prepTime <#Duration> ;
	schema:yield (<#QuantitativeValue> OR <#Text>) ;
	schema:performTime <#Duration> ;
	schema:estimatedCost (<#MonetaryAmount> OR <#Text>) ;
	schema:totalTime <#Duration> ;
}
```
## SHACL example

```python
from schema_validation.shapes_generator import ShapesGenerator


schema = json.loads(open(os.path.join(base_path, 'schema.jsonld')).read())
gen = ShapesGenerator(schema=schema)
print(gen.to_shacl('http://schema.org/HowTo'))
```
**Result:**
```
:HowTo sh:NodeShape;
	sh:targetClass schema:HowTo;
	sh:and (
		:CreativeWork
		sh:property [
			sh:path schema:step;
			sh:or (
				[sh:class :HowToStep]
				[sh:class :Text]
				[sh:class :CreativeWork]
				[sh:class :HowToSection]
			);
		]
		sh:property [
			sh:path schema:steps;
			sh:or (
				[sh:class :CreativeWork]
				[sh:class :ItemList]
				[sh:class :Text]
			);
		]
		sh:property [
			sh:path schema:supply;
			sh:or (
				[sh:class :HowToSupply]
				[sh:class :Text]
			);
		]
		sh:property [
			sh:path schema:tool;
			sh:or (
				[sh:class :HowToTool]
				[sh:class :Text]
			);
		]
		sh:property [
			sh:path schema:prepTime;
			sh:class :Duration;
		]
		sh:property [
			sh:path schema:yield;
			sh:or (
				[sh:class :QuantitativeValue]
				[sh:class :Text]
			);
		]
		sh:property [
			sh:path schema:performTime;
			sh:class :Duration;
		]
		sh:property [
			sh:path schema:estimatedCost;
			sh:or (
				[sh:class :MonetaryAmount]
				[sh:class :Text]
			);
		]
		sh:property [
			sh:path schema:totalTime;
			sh:class :Duration;
		]).
```
