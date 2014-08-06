from django.core.management.base import BaseCommand
from police.models import Council, Convexhull
from police.utils import config
from django.contrib.gis.geos.polygon import Polygon
import csv
import os

class Command(BaseCommand):
    help = 'Loads the convex hulls from directory: '+config.convexhulls_dir

    def handle(self, *args, **options):
        if Convexhull.objects.count() == len(config.allcities):
            print "Convex hulls are already loaded!"
            print "Doing nothing..."
            return
        
        allfiles = [f for f in os.listdir(config.convexhulls_dir) 
                    if os.path.isfile(os.path.join(config.convexhulls_dir,f)) and
                    ".csv" in f]
    
        for f in allfiles:
            fn = config.convexhulls_dir+f
            print "Storing convex hull from file:", fn
            
            _name = f[0:-21]
            ifile = open(fn, "rb")
            reader = csv.reader(ifile)
            lr = []
            for row in reader:
                entry = []
                for col in row: 
                    entry.append(col)
                
                lr.append((float(entry[0]), float(entry[1])))
                
            poly = Polygon(lr)
            
            ch = Convexhull(name = _name, poly = poly)
            ch.save()
            
            foundCouncil = False
            
            # Store the council foreign keys
            for allName in config.allcities.keys():
                if foundCouncil:
                    break;
                if _name in allName:
                    councils = Council.objects.filter(name=allName)
                    for council in councils:
                        council.convexhull = ch
                        council.save()
                        foundCouncil = True
                        
            if not foundCouncil:
                for allName in config.greater_london:
                    councils = Council.objects.filter(name=allName)
                    for council in councils:
                        council.convexhull = ch
                        council.save()
        