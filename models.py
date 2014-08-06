from django.contrib.gis.db import models
from django.contrib.gis.geos.point import Point
from police.utils.ShpParser import ShpParser

class MapPoints(models.Model):
    dIndex = models.BigIntegerField()
    userId = models.BigIntegerField()
    dbTime = models.DateField()
    reportTime = models.DateField()
    appVer = models.DecimalField(max_digits=2, decimal_places=1)
    lat = models.DecimalField(max_digits=20, decimal_places=17)
    lon = models.DecimalField(max_digits=20, decimal_places=17)
    description = models.CharField(max_length=256)
    firstCat = models.BigIntegerField()
    secCat = models.BigIntegerField()
    level = models.BigIntegerField()
    accuracy = models.DecimalField(max_digits=10, decimal_places=2)
    locationSource = models.BigIntegerField()
    reporttype = models.BigIntegerField() # changed name from "type" in original
    address = models.CharField(max_length=256)
    hazardType = models.CharField(max_length=256)
    activity = models.CharField(max_length=256)
    locationType = models.CharField(max_length=256)
    imei = models.BigIntegerField()
    isAlone = models.BigIntegerField()
    isMoving = models.BigIntegerField()
    
    neighbourhood = models.ForeignKey("Neighbourhood", null = True, blank = True)
    
    def __init__(self, *args, **kwargs):
        super(MapPoints, self).__init__(*args, **kwargs)
        shp = ShpParser()
        tmp_point = shp.convert_point_to_OSGB36(self.lat, self.lon)
#        print "converted point: ", point
        self.pt = Point(float(tmp_point[0]), float(tmp_point[1]), srid=27700)
    
    def __unicode__(self):
        return "MapPoint %s" % str(self.lat)+", "+str(self.lon)
    
#    def pt(self):
#        return Point(float(self.lat), float(self.lon))
    
    objects = models.GeoManager()

class Crimepoint(models.Model):
    crimecat = models.TextField()
    pt = models.PointField(srid = 27700)
    streetname = models.TextField()
    month = models.DateField()
    neighbourhood = models.ForeignKey("Neighbourhood", null = True, blank = True)
    
    objects = models.GeoManager()
    
    def __unicode__(self):
        return "Crimepoint #%s" % self.pt

class Postcode(models.Model):
    name = models.TextField()
    poly = models.MultiPolygonField(srid = 27700)

    objects = models.GeoManager()

    def __unicode__(self):
        return "Postcode #%s" % self.name
    
class Neighbourhood(models.Model):
    name = models.TextField()
    poly = models.MultiPolygonField(srid = 27700)
    council = models.ForeignKey("Council", null = True, blank = True)

    objects = models.GeoManager()

    def __unicode__(self):
        return "Neighbourhood #%s" % self.id

class Council(models.Model):
    name = models.TextField()
    poly = models.MultiPolygonField(srid = 27700)
    convexhull = models.ForeignKey("Convexhull", null = True, blank = True)
    
    objects = models.GeoManager()
    
    def __unicode__(self):
        return "Council #%s" % self.id
    
class Convexhull(models.Model):
    name = models.TextField()
    poly = models.PolygonField()
    
    objects = models.GeoManager()
    
    def __unicode__(self):
        return "Convexhull #%s" % self.id
    
class Statistics(models.Model):
    name = models.TextField()
    stat = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __unicode__(self):
        return self.name+": "+str(self.stat)