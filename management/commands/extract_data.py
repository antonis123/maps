from django.core.management.base import BaseCommand
from django.db.models.aggregates import Count
from optparse import make_option
from police.models import Crimepoint
from police.utils import config
import csv

class Command(BaseCommand):
    help = 'Extracts the crime incidents grouped by type and date, for a given region or city'
    regions = ["South-east", "South-west", "Midlands", "North", "London"]
    option_list = BaseCommand.option_list + (
        make_option('--region=',
            action='store',
            dest='region',
            default='None',
            help="Region to extract data for. Valid options: "+', '.join(regions)),
        ) + (
        make_option('--city=',
            action='store',
            dest='city',
            default='None',
            help='City to extract data for'),
        )

    def handle(self, *args, **options):
        if options['city'] is not 'None':
            print "Extracting data for city:", options['city']
            self.extractCity(options['city'])
        elif options['region'] is not 'None':
            if options['region'] in self.regions:
                print "Extracting data for region:", options['region']
                self.extractRegion(options['region'])
            else:
                print "Valid regions are:", self.regions
        else:
            print "Doing nothing."
            
    def extractCity(self, city):
        crimes = Crimepoint.objects.filter(neighbourhood__council__convexhull__name=city
                                           ).distinct(
                                           ).values("crimecat", "month"
                                                    ).annotate(Count("month"))
        
        fname = config.statDir+city+"_data.csv"
        ofile = open(fname, 'wb')
        print "Writing in file:", fname
        w = csv.writer(ofile)
        w.writerow(["Month"]+config.crimetypes+["Total"])
        
        dict = {}
        for c in crimes:
            month = str(c['month'])
            cat = c['crimecat']
            count = c['month__count']
            if dict.has_key(month):
                dict[month][cat] = count
                dict[month]['total'] += count
            else:
                dict[month] = {}
                for crimetype in config.crimetypes:
                    dict[month][crimetype] = 0 
                dict[month][cat] = count
                dict[month]['total'] = count
                
        for key, val in sorted(dict.iteritems()):
            entry = [key]
            for crimetype in config.crimetypes:
                entry.append(val[crimetype])
            entry.append(val['total']) 
            w.writerow(entry)
            
        ofile.close()
        
    def extractRegion(self, region):
        cities = []
        if region == "South-east":
            cities = ["Oxford", "Southampton UA", "Brighton and Hove UA"]
        elif region == "South-west":
            cities = ["Bristol, City of UA", "Bath and North East Some", "Plymouth UA"]
        elif region == "Midlands":
            cities = ["Birmingham", "Coventry", "Nottingham UA"]
        elif region == "North":
            cities = ["Liverpool", "Manchester", "Leeds"]
        else:
            cities = ["Greater London", "City of London"]
        
        crimes = Crimepoint.objects.filter(neighbourhood__council__convexhull__name__in=cities
                                           ).distinct(
                                           ).values("crimecat", "month"
                                                    ).annotate(Count("month"))
                     
        fname = config.statDir+region+"_data.csv"                              
        ofile = open(fname, 'wb')
        print "Writing to file:", fname
        w = csv.writer(ofile)
        w.writerow(["Month"]+config.crimetypes+["Total"])
        
        dict = {}
        for c in crimes:
            month = str(c['month'])
            cat = c['crimecat']
            count = c['month__count']
            if dict.has_key(month):
                dict[month][cat] = count
                dict[month]['total'] += count
            else:
                dict[month] = {}
                for crimetype in config.crimetypes:
                    dict[month][crimetype] = 0 
                dict[month][cat] = count
                dict[month]['total'] = count
                
        for key, val in sorted(dict.iteritems()):
            entry = [key]
            for crimetype in config.crimetypes:
                entry.append(val[crimetype])
            entry.append(val['total']) 
            w.writerow(entry)
            
        ofile.close()
        