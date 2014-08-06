'''
Created on 29 Jun 2012

@author: anb
'''
from django.contrib.gis.geos.point import Point
from police.models import Neighbourhood, Crimepoint
from police.utils import config
from police.utils.ShpParser import ShpParser
import calendar
import csv
import datetime
import re

def getAllPolice():
    police = []
    for val in config.allcities.values():
        if type(val[0]) == str:
            police.append(val[0])
            
    return police

def addMonths(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])
    return datetime.date(year,month,day)

def find_whole_word(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def approx_equal(a, b):
    return abs(a-b) < 0.0000001

def str_tokenize(s, delim):
    return re.split(delim, s)

def filter_crime_file(filename, poly, inDir, outDir, storeFlag=False):
    ifile = open(inDir+filename, "rb")
    reader = csv.reader(ifile)
    filteredFilename = outDir+filename[0:(len(filename)-4)]+"_filtered.csv"
    ofile = open(filteredFilename, 'a')
    writer = csv.writer(ofile)
    print "utilities - filterCrimeFile: Writing output to file", "\'" + ofile.name + "\'..."
    
    rownum = 0
    for row in reader:
        # Skip header row.
        if rownum != 0:
            colnum = 0
            point = [0 for x in xrange(2)]
            try:
                for col in row:
                    if (colnum == 3): point[0] = float(col)
                    elif (colnum == 4): point[1] = float(col)
                    colnum += 1
            except ValueError:
                print "Skipping badly formatted row:", row
                continue    
                
            # If we are filtering Greater London then 'poly' will be a list     
            if isinstance(poly, list):
                for polygon in poly:
                    if (polygon.contains(point[0], point[1])):
                        writer.writerow(row)
                        if storeFlag:
                            store(row)
                        break
            else:
                if (poly.contains(point[0], point[1])):
                    writer.writerow(row)
                    if storeFlag:
                        store(row)
        
        rownum += 1

    ifile.close()
    ofile.close()
    
    print "Done"
    
    return filteredFilename

'''
Stores an entry from a crime csv file to the database
'''
def store(row):
    shp = ShpParser(None)
    entry = []
    for col in row:
        entry.append(col)
        
    pts = shp.convert_point_to_WGS84(entry[3], entry[4])
    point = Point(float(entry[3]), float(entry[4]), srid=27700)
    neighbourhoods = Neighbourhood.objects.filter(poly__contains=point)
    
    nb = None
    
    if len(neighbourhoods) >= 1:
        nb = neighbourhoods[0]
    # Else the crime is not covered by any neighbouhood polygon (e.g. River thames)
    
    # Convert to format YYYY-MM-DD by replacing all occurences of "/" with "-".
    d = entry[0]
    d = d.replace('/', '-')
    d += "-01"

    c = Crimepoint(crimecat=entry[6], pt = Point(pts[1], pts[0]), 
                   streetname=entry[5], month=d, 
                   neighbourhood=nb)
    c.save()
