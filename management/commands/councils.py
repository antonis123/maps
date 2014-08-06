from django.contrib.gis.utils.layermapping import LayerMapping
from django.core.management.base import BaseCommand
from optparse import make_option
from police.models import Council
from police.utils import config

class Command(BaseCommand):
    help = 'Loads the council boundaries from: '+config.boundaries_file
    option_list = BaseCommand.option_list + (
        make_option('-a',
            action='store_true',
            dest='all',
            default=False,
            help='Load and clean the council polygons'),
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
            print "Loading and cleaning the council polygons..."
            self.load()
            self.clean()
        elif options['load']:
            print "Loading the council polygons..."
            self.load()
        elif options['clean']:
            print "Cleaning the council polygons..."
            self.clean()
        else:
            print "Doing nothing."
            
    def load(self):
        if Council.objects.count() > 0:
            print "Councils are already loaded!"
            return
        
        councils_mapping = {
            'name' : 'NAME',
            'poly': 'POLYGON'
        }
        lm = LayerMapping(Council, config.boundaries_file, 
                      councils_mapping, transform=False, encoding='iso-8859-1')
        lm.save(silent=False)
        
    def clean(self):
        saved = {}
        for council in Council.objects.all():
            found = False
            for name in config.allcities.keys() + config.greater_london:
                if name.lower()==council.name.lower():
                    found = True
                    # In case of duplicates we always keep the one with the most vertices
                    if saved.has_key(name):
                        if saved[name].poly.num_points < council.poly.num_points:
                            saved[name].delete()
                            saved[name] = council
                        else:
                            council.delete()
                    else:
                        saved[name] = council
                    
                    break
            if not found:
                council.delete()
        