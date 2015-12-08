'''
Created on 16 Oct 2015

@author: tb7554
'''

from __future__ import print_function
import xml.etree.ElementTree as ET

def convert(XMLnode, XMLedge, outputGEXF):
    
    nodeData = ET.parse(XMLnode)
    nodes = nodeData.getroot()
    
    edgeData = ET.parse(XMLedge)
    edges = edgeData.getroot()
    
    GEXF = open(outputGEXF, 'w')
    
    print("""<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2" xmlns:viz="http://www.gexf.net/1.2draft/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd">
  <meta lastmodifieddate="2009-03-20">
    <creator>Gexf.net</creator>
      <description>A hello world! file</description>
  </meta>
    <graph mode="static" defaultedgetype="directed">
      <nodes>""", file=GEXF)
    
    for node in nodes:
        name = node.attrib['id']
        x = float(node.attrib['x'])
        y = float(node.attrib['y'])
         
        print('''      <node id="%s" label="%s">
        <attvalues></attvalues>
        <viz:size value="10.0"></viz:size>
        <viz:position x="%f" y="%f" z="0.0"></viz:position>
        <viz:color r="0" g="0" b="0"></viz:color>
      </node>''' % (name, name, x, y), file = GEXF)

    print('\t</nodes>', file=GEXF)
    print('\t<edges>', file=GEXF)

    for edge in edges:
        name = edge.attrib['id']
        source = edge.attrib['from']
        target = edge.attrib['to'] 
        print('\t  <edge id="%s" source="%s" target="%s">' % (name, source, target), file=GEXF)
        print('\t  </edge>', file=GEXF)
            
    print('''\t</edges>'
  </graph>
</gexf>''', file=GEXF)

    GEXF.close()
    
def main():
    convert("/Users/tb7554/UniversityCloud/Home/workspace/_009_Grid-10x10_/netXMLFiles/Scalefree-10x10.nod.xml", "/Users/tb7554/UniversityCloud/Home/workspace/_009_Grid-10x10_/netXMLFiles/Scalefree-10x10.edg.xml", "/Users/tb7554/UniversityCloud/Home/workspace/_009_Grid-10x10_/netXMLFiles/Scalefree-10x10.gexf")
    

if __name__ == "__main__":
    main()