from django.contrib.gis.utils.layermapping import LayerMapping
from django.core.management.base import BaseCommand
from optparse import make_option
from police.models import Council, Neighbourhood, Crimepoint
from police.utils import config

class Command(BaseCommand):
    help = 'Loads the neighbourhood boundaries from: '+config.neighbourhoods
    option_list = BaseCommand.option_list + (
        make_option('-a',
            action='store_true',
            dest='all',
            default=False,
            help='Load and process the neighbourhood polygons'),
        ) + (
        make_option('-l',
            action='store_true',
            dest='load',
            default=False,
            help='Only load'),
        ) + (
        make_option('-c',
            action='store_true',
            dest='process',
            default=False,
            help='Only process'),
        )

    def handle(self, *args, **options):
        if options['all']:
            print "Loading and processing the neighbourhood polygons..."
            self.load()
            self.process()
        elif options['load']:
            print "Loading the neighbourhood polygons..."
            self.load()
        elif options['process']:
            print "Processing the neighbourhood polygons..."
            self.process()
        else:
            print "Doing nothing."
            
    def load(self):
        if Neighbourhood.objects.count() > 0:
            print "Neighbourhoods are already loaded!"
            return
        
        neighbourhood_mapping = {
            'name' : 'MSOA04NM',
            'poly' : 'POLYGON'
        }
        
        lm = LayerMapping(Neighbourhood, config.neighbourhoods, 
                      neighbourhood_mapping, transform=False, encoding='iso-8859-1')
        lm.save(silent=False)
        
    '''
    Filter-out unwanted neighbourhood polygons
    '''
    def process(self):
        ct = 1
    
        for n in Neighbourhood.objects.filter(council=None):
            crimes = Crimepoint.objects.filter(neighbourhood=n)
            
            """ 
            Only process neighbourhoods for which we don't have any crimes allocated yet.
            Otherwise there is the risk of deleting crimes as well!!!
            """
            if len(crimes) == 0:
                councils = None
                if "City of London" in n.name:
                    """
                    I treat the "City of London" as a special case, because it's neighbourhood polygon
                    intersects other council polygons as well so If I left it then points of Greater London
                    would me mixed into and vice versa.
                    """
                    councils = Council.objects.filter(name="City of London")
                else:
                    centroid = n.poly.centroid
                    councils = Council.objects.filter(poly__contains=centroid)
                    
                if (councils.count() == 0):
                    n.delete()
                elif councils.count() > 1:
                    print "count:", councils.count(), "neighbourhood:", n.name
                    print "council:", [c.name for c in councils]
                else:
                    n.council = councils[0]
                    n.save()
                
                if ct % 1000 == 0: print ct
                ct += 1
        