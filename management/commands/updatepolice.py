from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from optparse import make_option
from os.path import basename
from police.models import Crimepoint, Neighbourhood, Postcode
from police.utils import config, utilities
from police.utils.Polygon import Polygon
from police.utils.ShpParser import ShpParser
from police.utils.utilities import filter_crime_file
from urlparse import urlsplit
import csv
import datetime
import httplib2
import json
import os
import urllib2
import zipfile

class Command(BaseCommand):
    help = 'Updates the police crime incident database'
    option_list = BaseCommand.option_list + (
        make_option('-a',
            action='store_true',
            dest='all',
            default=False,
            help='Download, unzip, filter and store everything'),
        ) + (
        make_option('-d',
            action='store_true',
            dest='download',
            default=False,
            help='Download'),
        ) + (
        make_option('-u',
            action='store_true',
            dest='unzip',
            default=False,
            help='Unzip'),
        ) + (
        make_option('-f',
            action='store_true',
            dest='filter',
            default=False,
            help='Filter'),
        ) + (
        make_option('-s',
            action='store_true',
            dest='store',
            default=False,
            help='Store'),
        ) + (
        make_option('-c',
            action='store_true',
            dest='clean',
            default=False,
            help='Clean everything'),
        ) + (
        make_option('--city=',
            action='store',
            dest='city',
            default='None',
            help='Apply the operation only to the given city'),
        )
    
    def handle(self, *args, **options):
        http = httplib2.Http()
        http.add_credentials(config.police_user, config.police_pass)
        response, content = http.request(
            "http://policeapi2.rkh.co.uk/api/crime-last-updated",
            "GET"
        )
        police_date = json.loads(content)['date']
        police_date = datetime.datetime.strptime(police_date, '%Y-%m-%d').date()
        print "Police database last update:", police_date
        
        try:
            file_date = os.path.getmtime(config.lastUpdatedFile)
            file_date = datetime.date.fromtimestamp(file_date)
        except:
            # If this is the first time
            file_date = datetime.datetime.strptime("2010-12-01", '%Y-%m-%d').date()
        print "Local database last update:", file_date
            
        if options['all']:
            print "Doing everything..."
            
            if police_date > file_date:
                self.update(file_date, police_date)
                self.unzip()
                self.filter_crimes(True)
                self.touch(config.lastUpdatedFile)
            else:
                print "The police crime database is up to date."
        elif options['download']:
            print "Downloading..."
            
            if police_date > file_date:
                self.update(file_date, police_date)
            else:
                print "There is nothing new to download."
        elif options['unzip']:
            print "Unzipping..."
            self.unzip()
        elif options['filter']:
            if options['city'] is not 'None':
                print "Filtering crimes for city:", options['city']
                self.filter_crimes(c = options['city'])
            else:
                print "Filtering..."
                self.filter_crimes()
        elif options['store']:
            if options['city'] is not 'None':
                print "Storing crimes for city:", options['city']
                self.store(options['city'])
            else:
                print "Storing..."
                self.store()
                self.touch(config.lastUpdatedFile)
        elif options['clean']:
            print "Cleaning..."
            self.clean()
        else:
            print "Doing nothing."
    
    def touch(self, filename, times = None):
        with file(filename, 'a'):
            os.utime(filename, times)
    
    def url2name(self, url):
        return basename(urlsplit(url)[2])
    
    def download(self, url, localFileName = None):
        localName = self.url2name(url)
        req = urllib2.Request(url)
        try:
            r = urllib2.urlopen(req)
            if r.info().has_key('Content-Disposition'):
                # If the response has Content-Disposition, we take file name from it
                localName = r.info()['Content-Disposition'].split('filename=')[1]
                if localName[0] == '"' or localName[0] == "'":
                    localName = localName[1:-1]
            elif r.url != url: 
                # if we were redirected, the real file name we take from the final URL
                localName = self.url2name(r.url)
            if localFileName: 
                # we can force to save the file as specified name
                localName = localFileName
            f = open(localName, 'wb')
            f.write(r.read())
            f.close()
        except:
            print "Couldn't download file:",url
            
    def update(self, pastDate, newDate):
        while (pastDate < newDate):
            pastDate = utilities.addMonths(pastDate, 1)
            for pol in utilities.getAllPolice():
                url = (config.police_data_url+
                       "%02d-%02d/%02d-%02d-%s-street.zip" 
               % (pastDate.year, pastDate.month, pastDate.year, pastDate.month, pol))
                print "Downloading:", url
                fn = config.dataDir+pol+"-"+str(pastDate)+".zip"
                if (not os.path.exists(fn)):
                    self.download(url, fn)
                else:
                    print "File exists:", fn 
                
        print pastDate
        print newDate
        
    def unzip(self):
        allfiles = [f for f in os.listdir(config.dataDir) 
                    if os.path.isfile(os.path.join(config.dataDir,f)) and
                    ".zip" in f]
        
        for f in allfiles:
            fn = config.dataDir+f
            try:
                os.system("unzip -j "+fn+" -d "+config.csvDir)
            except zipfile.BadZipfile as e:
                print "Could not unzip file:", fn
              
    def filter_crimes(self, store=False, city=None):
        if city is None:
            for city in config.allcities.keys():
                polyFile = city+"_OSGB36_polygon.csv"
                polygon = None
                if city == "Greater London":
                    polygon = Polygon(config.greater_london_out_dir+polyFile)
                else:
                    polygon = Polygon(config.poly_dir+polyFile)
                crimeFiles = [f for f in os.listdir(config.csvDir) if 
                             os.path.isfile(os.path.join(config.csvDir,f)) and
                             config.allcities[city][0] in f]
                
                for crimefile in crimeFiles:
                    filter_crime_file(crimefile, polygon, config.csvDir, config.filteredDir, store)
        else:
            polyFile = city+"_OSGB36_polygon.csv"
            polygon = None
            if city == "Greater London":
                polygon = Polygon(config.greater_london_out_dir+polyFile)
            else:
                polygon = Polygon(config.poly_dir+polyFile)
            crimeFiles = [f for f in os.listdir(config.csvDir) if 
                         os.path.isfile(os.path.join(config.csvDir,f)) and
                         config.allcities[city][0] in f]
            
            print crimeFiles
            
            for crimefile in crimeFiles:
                filter_crime_file(crimefile, polygon, config.csvDir, config.filteredDir, store)
                
    def store(self, city=None):
        c = '' if city is None else str(city)
        allfiles = [f for f in os.listdir(config.filteredDir) 
                    if os.path.isfile(os.path.join(config.filteredDir,f)) and
                    (".csv" in f) and (c in f)]
        
        print "Storing crimes..."
        print "c:", c
        print "allfiles:", allfiles
        count = 0;
        
        for f in allfiles:
            ifile = open(config.filteredDir+f, "rb")
            reader = csv.reader(ifile)
            shp = ShpParser(None)
            print "Storing from file:", config.filteredDir+f
            for row in reader:
                entry = []
                for col in row:
                    entry.append(col)
                    
                assert(len(entry) == 8)
                
                pts = shp.convert_point_to_WGS84(entry[3], entry[4])
                point = Point(float(entry[3]), float(entry[4]), srid=27700)
                
                neighbourhoods = Neighbourhood.objects.filter(poly__intersects=point)
                
                nb = None
                
                if len(neighbourhoods) == 0:
                    # Else the crime is not covered by any neighbouhood polygon (e.g. River thames)
                    print "No neighbourhood found for point:", pts, "OSGB36:", point
                elif len(neighbourhoods) == 1:
                    nb = neighbourhoods[0]
                else:
#                    print "More than one polygons (",len(neighbourhoods),")  found for point:", pts, "OSGB36:", point
                    nb = neighbourhoods[0]
                
                # Convert to format YYYY-MM-DD by replacing all occurences of "/" with "-".
                d = entry[0]
                d = d.replace('/', '-')
                d += "-01"

                c = Crimepoint(crimecat=entry[6], pt = point, 
                               streetname=entry[5], month=d, 
                               neighbourhood=nb)
                c.save()
                    
                count += 1
            
        print "Stored", count, "crimes."
        
    '''
    Delete all intermediate files: downloaded/zipped, unzipped/unfiltered, filtered
    '''
    def clean(self):
        allfiles = [f for f in os.listdir(config.dataDir) 
                    if os.path.isfile(os.path.join(config.dataDir,f)) and
                    ".zip" in f]
        for f in allfiles:
            fn = config.dataDir+f
            os.remove(fn)
            
        crimeFiles = [f for f in os.listdir(config.csvDir) if 
                      os.path.isfile(os.path.join(config.csvDir,f)) and ".csv" in f]
        for crimefile in crimeFiles:
            os.remove(config.csvDir+crimefile)
        
        allfiles = [f for f in os.listdir(config.filteredDir) 
                    if os.path.isfile(os.path.join(config.filteredDir,f)) and
                    ".csv" in f]
        for f in allfiles:
            os.remove(config.filteredDir+f)
            
            
            
            