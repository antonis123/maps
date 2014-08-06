'''
Created on 29 Jun 2012

@author: anb

Instances of this class represent polygons
'''
from police.utils.utilities import approx_equal
import csv
import sys
    
class Polygon():
    
    # Reads a csv file, containing a polygon's points (in WGS84 coordinates)
    def __init__(self, filename):
        self.polygon = []
        
        ifile  = open(filename, "rb")
        reader = csv.reader(ifile)

        rownum = 0
        for row in reader:
            colnum = 0
            point = [0 for x in xrange(2)]
            for col in row:
                try:
                    point[colnum] = float(col);
                    colnum += 1
                except:
                    print sys.exc_info()
                    print "\'"+col+"\'"
                    print "filename:", filename, "row:", rownum, "col:", colnum
            
            self.polygon.append(point)
            rownum += 1

        ifile.close()
        print "Polygon - __init__: size of array:", len(self.polygon)
    
    # Point in Polygon: Determine if a point (lng, lat) is inside the polygon
    def contains(self, x, y):
        n = len(self.polygon)
        inside = False
        
        p1x, p1y = self.polygon[0]
        for i in range(n+1):
            p2x,p2y = self.polygon[i % n]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            
            # The point being queried lies exactly on a vertex                
            if approx_equal(x, p1x) and approx_equal(y, p1y):
                inside = True
            p1x,p1y = p2x,p2y

        return inside
    
    def toArray(self):
        return self.polygon