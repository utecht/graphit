import rdflib
import argparse
from rdflib.namespace import RDF, Namespace, NamespaceManager

parser = argparse.ArgumentParser(
        description='Produce graphviz dot file from RDF individuals.')
parser.add_argument('rdf',
        help='the rdf individuals to be graphed')
parser.add_argument('ontology',
        help='the ontology file for class names')
parser.add_argument('output',
        help='where to write the dot file')
parser.add_argument('--uri',
        help='restrict output to triples related to URI')
parser.add_argument('--depth',
        help='depth to restrict output from related URI', type=int, default=1)
parser.add_argument('--simple',
        help='simplify output', action='store_true')

args = parser.parse_args()

graph = rdflib.Graph()
graph.parse(args.rdf)

ontology = rdflib.Graph()
ontology.parse(args.ontology)

obo_namespace = NamespaceManager(ontology)

data = {}

def clean(text):
    ret = text.replace('<', '\<')
    ret = ret.replace('>', '\>')
    return ret

def q_name(uri):
    return obo_namespace.normalizeUri(uri)

length = 25
def wrap(text):
    if len(text) > length:
        start = text[:length]
        end = text[length:]
        return "{}\l{}".format(start, wrap(end))
    else:
        return text

def calc_depth(g, start):
    tbd_nodes = {start: 0}
    depths = {}
    while len(tbd_nodes) > 0:
        node, cur_depth = tbd_nodes.popitem()
        depths[node] = cur_depth
        for neighbor in g.objects(node, None):
            if neighbor not in depths.keys() and neighbor not in tbd_nodes.keys():
                tbd_nodes[neighbor] = cur_depth + 1
        for neighbor in g.subjects(None, node):
            if neighbor not in depths.keys() and neighbor not in tbd_nodes.keys():
                tbd_nodes[neighbor] = cur_depth + 1
    return depths

subjects = graph.subjects()
if args.uri:
    #restrict subjects to only subjects with a depth of args.depth
    depths = calc_depth(graph, rdflib.URIRef(args.uri))
    subjects = []
    for subj in depths.keys():
        if depths[subj] <= args.depth:
            subjects.append(subj)

for subj in subjects:
    if(subj not in data.keys()):
        sub = subj
        subj = str(subj)
        data[subj] = {}
    for types in graph.objects(sub, RDF.type):
        if('types' not in data[subj].keys()):
            data[subj]['types'] = []
        t = {}
        t['label'] = str(ontology.label(types))
        t['qname'] = q_name(types)
        if(t not in data[subj]['types']):
            data[subj]['types'].append(t)
    for pred, obj in graph.predicate_objects(sub):
        if(type(obj) == rdflib.term.URIRef):
            if(pred == RDF.type):
                pass
            else:
                if('connections' not in data[subj].keys()):
                    data[subj]['connections'] = []
                conn = {}
                conn['label'] = str(ontology.label(pred))
                conn['qname'] = q_name(pred)
                conn['to'] = str(obj)
                if(conn not in data[subj]['connections']):
                    data[subj]['connections'].append(conn)
        else:
            if('data_property' not in data[subj].keys()):
                data[subj]['data_properties'] = []
            dp = {}
            dp['label'] = str(ontology.label(pred))
            dp['qname'] = q_name(pred)
            dp['value'] = str(obj)
            if(dp not in data[subj]['data_properties']):
                data[subj]['data_properties'].append(dp)
for i, d in enumerate(data.keys()):
    data[d]['short'] = 'g{}'.format(i)

with open(args.output, 'w') as f:
    f.write("digraph structs {\n")
    f.write('rankdir=LR;\n')
    for node in data:
        n = data[node]
        properties = ""
        if('data_properties' in n):
            for dp in n['data_properties']:
                properties += "|{}\l{}\l{}\l".format(wrap(dp['label']),
                                                     wrap(dp['qname']),
                                                     wrap(dp['value']))
        type_info = ""
        color = "orange"
        if('types' in n):
            for t in n['types']:
                label = ""
                qname = ""
                if 'label' in t:
                    label = t['label']
                if 'qname' in t:
                    qname = t['qname']
                type_info += "{}\l{}\l".format(wrap(label), clean(wrap(qname)))
                if(args.simple):
                    type_info = "{}\l".format(wrap(label))
                color = "blue"
        if(args.simple):
            f.write('{} [shape=record,label="{}",color={}]\n'.format(
                    n['short'], type_info, color))
        else:
            f.write('{} [shape=record,label="{}\l{}{}",color={}]\n'.format(
                    n['short'], wrap(node), type_info, properties, color))
        if('connections' in n):
            for conn in n['connections']:
                if(conn['to'] in data):
                    conn_name = data[conn['to']]['short']
                    label = ''
                    qname = ''
                    if 'label' in conn:
                        label = conn['label']
                    if 'qname' in conn:
                        qname = conn['qname']
                    conn_details = '{}\l{}\l'.format(label, qname)
                    if(args.simple):
                        conn_details = '{}\l'.format(label)
                    f.write('{} -> {} [label="{}"]\n'.format(
                            n['short'], conn_name, conn_details))
                else:
                    print('bad connection: {}'.format(conn))
    f.write("}")
