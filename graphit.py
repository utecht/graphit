import rdflib
from rdflib.namespace import RDF, Namespace, NamespaceManager

ontology = rdflib.Graph()
graph = rdflib.Graph()

obo = Namespace('http://purl.obolibrary.org/obo/')
obo_namespace = NamespaceManager(ontology)

ontology.parse('gathered.owl')
graph.parse('rdf.xml')

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

for subj in graph.subjects():
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

from pprint import pprint
pprint(data)

with open('out.dot', 'w') as f:
    f.write("digraph structs {\n")
    f.write('rankdir=LR;\n')
    for node in data:
        n = data[node]
        properties = ""
        if('data_properties' in n):
            for dp in n['data_properties']:
                properties += "|{}\l{}\l{}\l".format(wrap(dp['label']), wrap(dp['qname']), wrap(dp['value']))
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
                color = "blue"
        f.write('{} [shape=record,label="{}\l{}{}",color={}]\n'.format(n['short'], wrap(node), type_info, properties, color))
        #f.write('{} [shape=record,label="{}{}"]\n'.format(n['short'], type_info, properties))
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
                    f.write('{} -> {} [label="{}"]\n'.format(n['short'], conn_name, conn_details))
                else:
                    print('bad connection: {}'.format(conn))
    f.write("}")
