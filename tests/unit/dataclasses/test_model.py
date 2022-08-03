from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import FOAF, RDF

from buildingmotif import BuildingMOTIF
from buildingmotif.dataclasses import Library, Model, ValidationContext
from buildingmotif.namespaces import BRICK, RDFS, A

BLDG = Namespace("urn:building/")


def test_create_model(clean_building_motif):
    model = Model.create(name="my_model")

    assert isinstance(model, Model)
    assert model.name == "my_model"
    assert isinstance(model.graph, Graph)


def test_load_model(clean_building_motif):
    m = Model.create(name="my_model")
    m.graph.add((URIRef("http://example.org/alex"), RDF.type, FOAF.Person))

    result = Model.load(m.id)
    assert result.id == m.id
    assert result.name == m.name
    assert isomorphic(result.graph, m.graph)


def test_validate_model(clean_building_motif):
    # load library
    lib = Library.load(ontology_graph="tests/unit/fixtures/shapes/shape1.ttl")
    assert lib is not None

    BLDG = Namespace("urn:building/")
    m = Model.create(name=BLDG)
    m.add_triples((BLDG["vav1"], A, BRICK.VAV))

    ctx = m.validate([lib.get_shape_collection()])
    assert not ctx.valid

    m.add_triples((BLDG["vav1"], A, BRICK.VAV))
    m.add_triples((BLDG["vav1"], BRICK.hasPoint, BLDG["sensor"]))
    m.add_triples((BLDG["sensor"], A, BRICK.Temperature_Sensor))

    ctx = m.validate([lib.get_shape_collection()])
    assert ctx.valid


def test_model_validate(bm: BuildingMOTIF):
    """
    Test that a model correctly validates
    """
    shape_graph_data = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix : <urn:shape_graph/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
: a owl:Ontology .
:zone_shape a sh:NodeShape ;
    sh:targetClass brick:HVAC_Zone ;
    sh:message "all HVAC zones must have a label" ;
    sh:property [
        sh:path rdfs:label ;
        sh:minCount 1 ;
    ] .
    """
    shape_graph = Graph().parse(data=shape_graph_data)
    shape_lib = Library.load(ontology_graph=shape_graph)

    lib = Library.load(directory="tests/unit/fixtures/templates")
    zone = lib.get_template_by_name("zone")
    assert zone.parameters == {"name", "cav"}

    # create model from template
    model = Model.create(BLDG)
    bindings, hvac_zone_instance = zone.fill(BLDG)
    model.add_graph(hvac_zone_instance)

    # validate the graph (should fail because there are no labels)
    ctx = model.validate([shape_lib.get_shape_collection()])
    assert isinstance(ctx, ValidationContext)
    assert not ctx.valid

    model.add_triples((bindings["name"], RDFS.label, Literal("hvac zone 1")))
    # validate the graph (should now be valid)
    ctx = model.validate([shape_lib.get_shape_collection()])
    assert isinstance(ctx, ValidationContext)
    assert ctx.valid
