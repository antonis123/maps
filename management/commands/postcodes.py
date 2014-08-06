from django.contrib.gis.utils.layermapping import LayerMapping
from django.core.management.base import BaseCommand
from optparse import make_option
from police.models import Council, Postcode
from police.utils import config

class Command(BaseCommand):
    help = 'Loads the postcode boundaries from directory: '+config.postcodeDir
    option_list = BaseCommand.option_list + (
        make_option('-a',
            action='store_true',
            dest='all',
            default=False,
            help='Load and clean the postcode polygons'),
        ) + (
        make_option('-l',
            action='store_true',
            dest='load',
            default=False,
            help='Only load'),
        ) + (
        make_option('-c',
            action='store_true',
            dest='clean',
            default=False,
            help='Only clean'),
        )


    def handle(self, *args, **options):
        if options['all']:
            print "Loading and cleaning the postcode polygons..."
            self.load()
            self.clean()
        elif options['load']:
            print "Loading the postcode polygons..."
            self.load()
        elif options['clean']:
            print "Cleaning the postcode polygons..."
            self.clean()
        else:
            print "Doing nothing."
            
    def load(self):
        if Postcode.objects.count() > 0:
            print "Postcodes are already loaded!"
            return
        
        postcode_mapping = {
            'name' : 'POSTCODE',
            'poly' : 'POLYGON',
        }
        
        for s in config.postcodes:
            lm = LayerMapping(Postcode,
                              config.postcodeDir+s, postcode_mapping, transform=False, 
                              encoding='iso-8859-1')
            lm.save(silent=False)
        
    '''
    Filter-out unwanted postcode polygons
    '''
    def clean(self):
        ct = 1
    
        for b in Postcode.objects.all():
            centroid = b.poly.centroid
            if (Council.objects.filter(poly__contains=centroid).count() == 0):
                b.delete()
            
            if ct % 1000 == 0: print ct
            ct += 1
        