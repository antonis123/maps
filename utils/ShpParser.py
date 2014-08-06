'''
Created on 21 Jun 2012

@author: anb
'''
from police.utils.OSGB36toWGS84 import OSGB36toWGS84
from police.utils.WGS84toOSGB36 import WGS84toOSGB36
import csv
import shapefile
    
class ShpParser:
    
    def __init__(self, outDir = None):
        self.outDir = outDir
    
    '''
    Finds and returns a shape with the given name in
    contained in the given shapeStruct
    '''
    def find_shape(self, shapeStruct, name):
        shapes = shapeStruct.shapes()
        records = shapeStruct.records()
        results = []
        
        for index, record in enumerate(records):
            rec = record[0]
            if name.lower() in rec.lower():
                print "ShpParser - find_shape: found ", "\'" + rec + "\'", "at position: ", index
                results.append(index)
        
        if (len(results) == 1):
            return shapes[results[0]]
        else:
            # We found more than one shapes with the same search term
            print "ShpParser - find_shape: there are more than one shapes containing the search term:", name
            idxs = []
            for index, res in enumerate(results):
                print str(index+1)+":", records[res][0]
                idxs.append(index+1)
            
            while True:
                try:
                    choice = input("Choose one "+str(idxs)+":")
                    return shapes[results[choice-1]]
                except:
                    print "Invalid choice!"
                    
        return None
                
    # Converts given point list from OSGB36 to WGS84
    def convert_list_to_WGS84(self, pointList):
        pts = [[0 for x in xrange(2)] for x in xrange(len(pointList))]
        for index, point in enumerate(pointList):
            E = None
            N = None
            
            try:
                E = float(point[0]) # Eastings
                N = float(point[1]) # Northings
            except TypeError, err:
                E = point[0] # Eastings
                N = point[1] # Northings

            lat, lng = OSGB36toWGS84(E, N)
            
            pts[index][0] = lat
            pts[index][1] = lng
        
        return pts
    
    # Converts the given coordinates from OSGB36 to WGS84
    def convert_point_to_WGS84(self, e, n):
        pt = [0 for x in xrange(2)]
        
        E = None
        N = None
        
        try:
            E = float(e) # Eastings
            N = float(n) # Northings
        except TypeError, err:
            pass
        
        lat, lng = OSGB36toWGS84(E, N)
        ### Coord is now in lng/lat
        pt[0] = lat
        pt[1] = lng
        
        return pt
    
    # Converts the given coordinates from OSGB36 to WGS84
    def convert_point_to_OSGB36(self, lat, lng):
        pt = [0 for x in xrange(2)]
        
        E = None
        N = None
        
        try:
            E = float(lat) # Lat
            N = float(lng) # Lng
        except TypeError, err:
            E = lat # Lat
            N = lng # Lng
        
        e, n = WGS84toOSGB36(E, N)
        ### Coord is now in lng/lat
        pt[0] = e
        pt[1] = n
        
        return pt
    
    def write(self, filename, pts):
        ofile = open(self.outDir+filename, 'wb')
        w = csv.writer(ofile)
        print "ShpParser - write: Writing output to file", "\'" + ofile.name + "\'"
        for k, v in enumerate(pts):
            w.writerow(v)
        ofile.close()
    
    # Parses a shapefile containing OSGB36 polygon points and writes them to
    # a csv file. We can choose to convert the data to WGS84 by setting the flag 
    def parse(self, inFile, searchTerm, convertToWGS84):
        sf = shapefile.Reader(inFile)
        
        shape = self.find_shape(sf, searchTerm)
        
        if shape is not None:
            pointList = shape.points;
            print "ShpParser - parse: number of points:", len(pointList)
            
            if convertToWGS84:
                pointList = self.convert_list_to_WGS84(pointList)
                self.write(searchTerm + '_WGS84_polygon.csv', pointList)
            else:
                self.write(searchTerm + '_OSGB36_polygon.csv', pointList)
        else:
            print "ShpParser - parse: No shapes found for:", searchTerm

    
