'''
Created on 29 Jun 2012

@author: anb
'''
import sys
import xml.dom.minidom

def create_style_map(kmlDoc):
    styleMap = kmlDoc.createElement('StyleMap')
    styleMap.setAttribute("id", "msn_poly_style")
    styleMap.setIdAttribute("id")
    
    pair1 = kmlDoc.createElement('Pair')
    key1 = kmlDoc.createElement('key')
    key1.appendChild(kmlDoc.createTextNode("normal"))
    styleUrl1 = kmlDoc.createElement('styleUrl')
    styleUrl1.appendChild(kmlDoc.createTextNode("#sn_poly_style"))
    pair1.appendChild(key1)
    pair1.appendChild(styleUrl1)
    
    styleMap.appendChild(pair1)
    
    pair2 = kmlDoc.createElement('Pair')
    key2 = kmlDoc.createElement('key')
    key2.appendChild(kmlDoc.createTextNode("highlight"))
    styleUrl2 = kmlDoc.createElement('styleUrl')
    styleUrl2.appendChild(kmlDoc.createTextNode("#sh_poly_style"))
    pair2.appendChild(key2)
    pair2.appendChild(styleUrl2)
    
    styleMap.appendChild(pair2)
    
    return styleMap

def create_style(kmlDoc, val):
    style = kmlDoc.createElement('Style')
    style.setAttribute("id", val)
    style.setIdAttribute("id")
    
    polyStyle = kmlDoc.createElement('PolyStyle')
    color = kmlDoc.createElement('color')
    color.appendChild(kmlDoc.createTextNode('7fff0000'))
    polyStyle.appendChild(color)
    style.appendChild(polyStyle)
    
    return style

def create_poly_KML(csvReader, fileName):
    # This constructs the KML document from the CSV file.
    kmlDoc = xml.dom.minidom.Document()
    
    kmlElement = kmlDoc.createElementNS('http://earth.google.com/kml/2.2', 'kml')
    kmlElement.setAttribute('xmlns', 'http://earth.google.com/kml/2.2')
    kmlElement = kmlDoc.appendChild(kmlElement)
    documentElement = kmlDoc.createElement('Document')
    documentElement = kmlElement.appendChild(documentElement)
    
    nameElement = kmlDoc.createElement('name')
    nameElement.appendChild(kmlDoc.createTextNode(fileName[0:(len(fileName)-4)]))
    documentElement.appendChild(nameElement)
    
    placemarkElement = kmlDoc.createElement('Placemark')
    polygonElement = kmlDoc.createElement('Polygon')
    outerBoundaryIsElement = kmlDoc.createElement('outerBoundaryIs')
    linearRingElement = kmlDoc.createElement('LinearRing')
    coordinatesElement = kmlDoc.createElement('coordinates')
    
    documentElement.appendChild(create_style_map(kmlDoc))
    documentElement.appendChild(create_style(kmlDoc, "sn_poly_style"))
    documentElement.appendChild(create_style(kmlDoc, "sh_poly_style"))
    
    styleUrl = kmlDoc.createElement('styleUrl')
    styleUrl.appendChild(kmlDoc.createTextNode("#msn_poly_style"))
    placemarkElement.appendChild(styleUrl)
    
    linearRingElement.appendChild(coordinatesElement)
    outerBoundaryIsElement.appendChild(linearRingElement)
    polygonElement.appendChild(outerBoundaryIsElement)
    placemarkElement.appendChild(polygonElement)
    documentElement.appendChild(placemarkElement)
    
    coordinates = ""
    for row in csvReader:
        p1, p2 = row.split(",")
        r = p2.strip()+","+p1.strip()+"\n"
        print r
        coordinates += r
    
    coordinatesElement.appendChild(kmlDoc.createTextNode(coordinates))
    
    kmlFile = open(fileName, 'w')
    kmlFile.write(kmlDoc.toprettyxml('  ', newl = '\n', encoding = 'utf-8'))

def main():
    if (len(sys.argv) == 3):
        inputFile = sys.argv[1]
        fileName = sys.argv[2]
    else:
        print "Error: Wrong number of arguments!"
        sys.exit(0)
    
    csvreader = open(inputFile)
    kml = create_poly_KML(csvreader, fileName)

if __name__ == '__main__':
    main()