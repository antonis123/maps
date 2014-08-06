from django.core.management.base import BaseCommand
from optparse import make_option
from police.utils import config, convexhull
from police.utils.ShpParser import ShpParser
from sys import settrace
import os

class Command(BaseCommand):
    help = 'Extracts the polygons from the shp files'
    option_list = BaseCommand.option_list + (
        make_option('-a',
            action='store_true',
            dest='all',
            default=False,
            help='Extract polygons for all 13 cities'),
        ) + (
        make_option('--city=',
            action='store',
            dest='city',
            default='None',
            help='Extract a polygon only for the given city'),
        ) + (
        make_option('-c',
            action='store_true',
            dest='convexhull',
            default=False,
            help='Extract convex hulls for all 13 cities'),
        )

    def handle(self, *args, **options):
        settrace
        if options['all']:
            print "Extracting polygons for all 13 cities..."
            print "This is going to take some time..."
            self.extractAll()
        elif options['city'] is not 'None':
            print "Extracting polygon for city:", options['city']
            self.extractOne(options['city'])
        elif options['convexhull']:
            print "Extracting convex hulls for all 13 cities..."
            self.extractConvexhulls()
        else:
            print "Doing nothing."
            
    def extractOne(self, cityName):
        shp = ShpParser(config.poly_dir)
        shp.parse(config.boundaries_file, cityName, False)
        shp.parse(config.boundaries_file, cityName, True)
        
    def extractAll(self):
        shp = ShpParser(config.poly_dir)
        for city in config.allcities.keys():
            # Greater London is a special case as it has 32 councils
            if city != "Greater London":
                shp.parse(config.boundaries_file, city, False)
            
        shp = ShpParser(config.greater_london_out_dir)
        for borough in config.greater_london:
            shp.parse(config.boundaries_file, borough, False)
            
        pts = convexhull.merge(config.greater_london_out_dir)
        c = convexhull.convexHull(pts)
        shp.write('Greater London_OSGB36_polygon.csv', c)
        
    def extractConvexhulls(self):
        shp = ShpParser(config.convexhulls_dir)
        
        allfiles = [f for f in os.listdir(config.poly_dir) 
                    if os.path.isfile(os.path.join(config.poly_dir,f)) and
                    "OSGB36_polygon.csv" in f]
        
        for fn in allfiles:
            pts = convexhull.loadCSV(config.poly_dir+fn)
            pts = shp.convert_list_to_WGS84(pts)
            c = convexhull.convexHull(pts)
            shp.write(fn[0:-18]+"WGS84_convexhull.csv", c)
        
        name = "Greater London_OSGB36_polygon.csv"
        pts = convexhull.loadCSV(config.greater_london_out_dir+name)
        pts = shp.convert_list_to_WGS84(pts)
        shp.write(name[0:-18]+"WGS84_convexhull.csv", pts)
            



