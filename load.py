'''
Created on 6 Jul 2012

@author: anb
'''

from django.db.models.aggregates import Count, Avg
from police.models import Postcode, Council, Neighbourhood, Crimepoint, \
    Statistics, MapPoints
from police.utils import config
import csv
   
'''
Finds a neighbourhood association for all unassociated points in the db
'''
def process_crimepoints():
    ct = 1
    
    for c in Crimepoint.objects.filter(neighbourhood=None):
        neighbourhoods = Neighbourhood.objects.filter(poly__intersects=c.pt)
        if neighbourhoods.count() != 0:
            c.neighbourhood = neighbourhoods[0]
            c.save()
        
        if ct % 1000 == 0:
            print ct

        ct += 1
        
'''
Finds a neighbourhood association for all unassociated points (perception of fear
data) in the db
'''
def process_mappoints():
    ct = 1
    
    for c in MapPoints.objects.filter(neighbourhood=None):
        neighbourhoods = Neighbourhood.objects.filter(poly__intersects=c.pt)
        if neighbourhoods.count() != 0:
            c.neighbourhood = neighbourhoods[0]
            c.save()
        
        if ct % 1000 == 0:
            print ct

        ct += 1
     
'''
Loads the populations for the given cities in the database.
The cities along with their population have to be defined in the config file
'''
def populations(cities=config.allcities.keys()+["Greater London"]):
    for city in cities:
        print "Loading population for city:", city
        
        # Save the population of the city
        st = Statistics(name=city+"_population", stat=config.allcities[city][1])
        st.save()
        
'''
Calculates the intermediate statistics (min, max, ect.) for the given cities
and stores them in the database
'''
def calculate_statistics(cities=config.allcities.keys()+["Greater London"]):
    for city in cities:
        print "Calculating statistics for city:", city
        
        for crimetype in config.crimetypes:
            max_x = None
            min_x = None
            nb = Neighbourhood.objects.filter(council__convexhull__name=city)
            for n in nb:
                count = Crimepoint.objects.filter(neighbourhood=n).filter(crimecat=crimetype).count()
                if (max_x and min_x) is None:
                    max_x = count
                    min_x = count
                elif count > max_x:
                    max_x = count
                elif count < min_x:
                    min_x = count
                    
            max_x = "{0:.2f}".format(max_x)
            min_x = "{0:.2f}".format(min_x)
            _name = city+"_neighbourhood_min_"+crimetype
            st = Statistics(name=_name, stat=min_x)
            st.save()
            _name = city+"_neighbourhood_max_"+crimetype
            st = Statistics(name=_name, stat=max_x)
            st.save()
                            
            max_x = None
            min_x = None
            councils = Council.objects.filter(convexhull__name=city)
            postcodes = Postcode.objects.filter(poly__intersects=councils[0].poly)
            for p in postcodes:
                #Get all the crimes in this postcode
                count = Crimepoint.objects.filter(pt__within=p.poly).filter(crimecat=crimetype).count()
                if (max_x and min_x) is None:
                    max_x = count
                    min_x = count
                elif count > max_x:
                    max_x = count
                elif count < min_x:
                    min_x = count
                    
            max_x = "{0:.2f}".format(max_x)
            min_x = "{0:.2f}".format(min_x)
            _name = city+"_postcode_min_"+crimetype
            st = Statistics(name=_name, stat=min_x)
            st.save()
            _name = city+"_postcode_max_"+crimetype
            st = Statistics(name=_name, stat=max_x)
            st.save()
    
'''
Extracts statistical date for the given cities and stores them in the file
with the given filename
'''
def extract_data(filename, cities=config.allcities.keys()+["Greater London"]):
    crimes = Crimepoint.objects.filter(neighbourhood__council__convexhull__name__in=
                                       cities
                                       ).distinct(
                                       ).values("crimecat", "month"
                                                ).annotate(Count("month"))
                                                
    ofile = open(config.statDir+filename+"_data.csv", 'wb')
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
            
    print dict
            
    for key, val in sorted(dict.iteritems()):
        entry = [key]
        for crimetype in config.crimetypes:
            entry.append(val[crimetype])
        entry.append(val['total']) 
        w.writerow(entry)
        
    ofile.close()

'''
Extracts statistical information for all cities (each one in a seperate file)
and uses each city's name for the filename
'''
def extract_all():
    for c in config.allcities.keys()+["Greater London"]:
        extract_data(c, [c])   
        
'''
Extracts crime along with fear/perception data for any neighbourhood that
has fear/perception data associated with it
'''
def extract_data_neighbourhoods():
    for n in Neighbourhood.objects.all():
        # reporttype 4 is automatic reponse - no person present, so we ignore it
        senses = MapPoints.objects.exclude(reporttype=4).filter(neighbourhood=n)
        if senses.count() != 0:
            crimes = Crimepoint.objects.filter(neighbourhood=n).distinct(
                                                                        ).values("crimecat", "month"
                                                                        ).annotate(Count("month"))
                        
            fn = config.statDir+n.name+"_neighbourhood_data.csv"
            print "Writing file:", fn                      
            ofile = open(fn, 'wb')
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
                
            w.writerow('')
            w.writerow(['', 'count', 'average'])
            w.writerow(['Users', senses.values("userId").distinct().count()])
            w.writerow(['Records', senses.count()])
            w.writerow(['Secure', senses.filter(reporttype=1).count()] + senses.filter(reporttype=1).aggregate(Avg("level")).values())
            w.writerow(['Insecure', senses.filter(reporttype=2).count()] + senses.filter(reporttype=2).aggregate(Avg("level")).values())
            w.writerow(['Hazard', senses.filter(reporttype=3).count()] + senses.filter(reporttype=3).aggregate(Avg("level")).values())
            
            w.writerow(['Secure>=4', senses.filter(reporttype=1).filter(level__gte=4).count()])
            w.writerow(['Secure<=2', senses.filter(reporttype=1).filter(level__lte=2).count()])
            
            w.writerow(['Insecure>=4', senses.filter(reporttype=2).filter(level__gte=4).count()])
            w.writerow(['Insecure<=2', senses.filter(reporttype=2).filter(level__lte=2).count()])
            
            w.writerow(['Hazard>=4', senses.filter(reporttype=3).filter(level__gte=4).count()])
            w.writerow(['Hazard<=2', senses.filter(reporttype=3).filter(level__lte=2).count()])
                
            ofile.close()                      
