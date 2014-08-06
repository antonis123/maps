'''
Created on 27 Jun 2012

@author: anb

Used to generate Convex Hulls
'''

from police.utils.Polygon import Polygon
import os

######################################################################
# Helpers
######################################################################

def _myDet(p, q, r):
    """Calc. determinant of a special matrix with three 2D points.

    The sign, "-" or "+", determines the side, right or left,
    respectivly, on which the point r lies, when measured against
    a directed vector from p to q.
    """

    # We use Sarrus' Rule to calculate the determinant.
    # (could also use the Numeric package...)
    sum1 = q[0]*r[1] + p[0]*q[1] + r[0]*p[1]
    sum2 = q[0]*p[1] + r[0]*q[1] + p[0]*r[1]

    return sum1 - sum2


def _isRightTurn((p, q, r)):
    "Do the vectors pq:qr form a right turn, or not?"

    assert p != q and q != r and p != r
            
    if _myDet(p, q, r) < 0:
        return 1
    else:
        return 0


def _isPointInPolygon(r, P):
    "Is point r inside a given polygon P?"

    # We assume the polygon is a list of points, listed clockwise!
    for i in xrange(len(P[:-1])):
        p, q = P[i], P[i+1]
        if not _isRightTurn((p, q, r)):
            return 0 # Out!        

    return 1 # It's within!

######################################################################
# Public interface
######################################################################

def convexHull(P):
    "Calculate the convex hull of a set of points."

    # Remove any duplicates
    # If the hull has a duplicate point, it will be returned once
    # It is up to the application to handle it correctly
    unique = {}
    for p in P:
        t = (p[0], p[1])
        unique[t] = 1
    
    points = unique.keys()
    points.sort()
    
    print "Merged set length:", len(points)

    # Build upper half of the hull.
    upper = [points[0], points[1]]
    for p in points[2:]:
        upper.append(p)
        while len(upper) > 2 and not _isRightTurn(upper[-3:]):
            del upper[-2]

    # Build lower half of the hull.
    points.reverse()
    lower = [points[0], points[1]]
    for p in points[2:]:
        lower.append(p)
        while len(lower) > 2 and not _isRightTurn(lower[-3:]):
            del lower[-2]

    # Remove duplicates.
    del lower[0]
    del lower[-1]

    # Concatenate both halfs and return.
    res = list(upper + lower)
    res.append(res[0])
    
    return res

######################################################################

# Only keeps unique points
def merge(polyDir):
    allfiles = [f for f in os.listdir(polyDir) if os.path.isfile(os.path.join(polyDir,f))]
    mergedArray = []
    for fn in [f for f in allfiles if "polygon.csv" in f]:
        mergedArray = list(Polygon(polyDir+fn).toArray()+mergedArray)
        
    print "mergedArray length:", len(mergedArray)
    
    return mergedArray

def loadCSV(filename):
    return list(Polygon(filename).toArray())
