from __future__ import division
from PIL import Image, ImageDraw, ImageFilter
from django.contrib.gis import geos
from django.contrib.gis.geos.polygon import Polygon
from police.models import Neighbourhood, Postcode, Crimepoint, Council, \
    Statistics
from police.utils.ShpParser import ShpParser
import ModestMaps

GREEN = (90, 75, 50)
RED = (0, 100, 40)
NONE_COLOR = (210, 100, 40)
WHITE = "rgb(255, 255, 255)"
BLACK = "rgb(0, 0, 0)"
HEATMAP_MIN = 0
HEATMAP_MAX = 1

class CrimeHeatmapProvider:
    def __init__(self, layer, *args, **kwargs):
        self.layer = layer
        self.provider = ModestMaps.OpenStreetMap.Provider()
        self.type = kwargs['type']

    def renderArea(self, width, height, srs, xmin, ymin, xmax, ymax, zoom):
        # start drawing each block
        pil_map = Image.new("RGBA", (width, height), (255,255,255, 0))
        pil_draw = ImageDraw.Draw(pil_map)
        
        # return empty images
        if zoom < 11:
            return pil_map

        # first, figure out the bounding box of the tile we're rendering
        nw = self.layer.projection.projLocation(ModestMaps.Core.Point(xmin, ymin))
        se = self.layer.projection.projLocation(ModestMaps.Core.Point(xmax, ymax))
        max_lat = max(nw.lat, se.lat)
        min_lat = min(nw.lat, se.lat)
        max_lon = max(nw.lon, se.lon)
        min_lon = min(nw.lon, se.lon)
        
        # Converting polygon to OSGB36 in order to compare with the ones we have in
        # the database
        shp = ShpParser()
        min_p = shp.convert_point_to_OSGB36(min_lat, min_lon)
        max_p = shp.convert_point_to_OSGB36(max_lat, max_lon)
        
        bbox = Polygon.from_bbox((min_p[0], min_p[1], max_p[0], max_p[1]))
        
        # this obj is used to translate between lat/lon and pixel space
        bound1 = ModestMaps.Geo.Location(min_lat, min_lon)
        bound2 = ModestMaps.Geo.Location(max_lat, max_lon)
        mmap = ModestMaps.mapByExtentZoom(self.provider, bound1, bound2, zoom)

        neighbourhoods = False
        polys = None
        max_x = None
        min_x = None
        
        try:
            # If zoom < 15 we draw postcode polygons, otherwise neighbourhoods
            if zoom < 15 or self.type == "None":
                polys = Neighbourhood.objects.filter(poly__intersects=bbox)
                neighbourhoods = True
            else:
                polys = Postcode.objects.filter(poly__intersects=bbox)
                
            print "Painting", polys.count(), "blocks"
            
            # Have to find the city where the polygons belong in
            _city = None
            if self.type != "None":
                for poly in polys:
                    if _city is not None:
                        break
                    if poly.poly and isinstance(poly.poly, geos.MultiPolygon):
                        for inside_poly in poly.poly:
                            if _city is None:
                                # Find the city if we haven't found it yet
                                cities = Council.objects.filter(poly__intersects=inside_poly)
                                if len(cities) > 0:
                                    _city = cities[0].convexhull.name
                                    break
                    else: # Probably unneeded as eventually we only have Multipolygons in our db 
                        if _city is None:
                            # Find the city if we haven't found it yet
                            cities = Council.objects.filter(poly__intersects=inside_poly)
                            if len(cities) > 0:
                                _city = cities[0].convexhull.name
                                break
                        
            print "City:", _city
                
            if len(polys) > 0 and self.type != "None":        
                if neighbourhoods:
                    _name = _city+"_neighbourhood_max_"+self.type
                    max_x = float(Statistics.objects.filter(name=_name).all()[0].stat)
                    _name = _city+"_neighbourhood_min_"+self.type
                    min_x = float(Statistics.objects.filter(name=_name).all()[0].stat)
                else:
                    _name = _city+"_postcode_max_"+self.type
                    max_x = float(Statistics.objects.filter(name=_name).all()[0].stat)
                    _name = _city+"_postcode_min_"+self.type
                    min_x = float(Statistics.objects.filter(name=_name).all()[0].stat)
                        
                print "max:", max_x, "min:", min_x
                          
            # For all the polygons we've retrieved from the database (in OSGB36 format)
            for poly in polys:
                _city = None
                if poly.poly and isinstance(poly.poly, geos.MultiPolygon):
                    for inside_poly in poly.poly:
                        
                        if _city is None:
                            # Find the city if we haven't found it yet
                            cities = Council.objects.filter(poly__intersects=inside_poly)
                            if len(cities) > 0:
                                _city = cities[0].convexhull.name
    
                        self._paint_poly(inside_poly, shp, mmap, pil_draw, _city,
                                         max_x, min_x, neighbourhoods)
                else: # Probably unneeded as eventually we only have Multipolygons in our db 
                    if _city is None:
                        # Find the city if we haven't found it yet
                        cities = Council.objects.filter(poly__intersects=inside_poly)
                        if len(cities) > 0:
                            _city = cities[0].convexhull.name
                    self._paint_poly(poly.poly, shp, mmap, pil_draw, _city,
                                     max_x, min_x, neighbourhoods)
        except Exception, err:
            print err
        
        return pil_map
    
    def _paint_poly(self, poly, shp, mmap, pil_draw, _city, max_x, min_x, neighbourhoods=False):
        newPoly = []
        crimes = []
        # shape
        locs = []
        for c in poly.coords[0]:
            # Convert each point from easting, northing to lat, lng
            WGS84pt = shp.convert_point_to_WGS84(c[0], c[1])
            # Convert point to pixel space
            pt = ModestMaps.Geo.Location(WGS84pt[0], WGS84pt[1])
            newPoly.append((pt.lon, pt.lat))
            loc = mmap.locationPoint(pt)
            locs.append((loc.x, loc.y))
                           
        if self.type != "None":                     
            # Number of crimes of that type in the polygon 
            crimes = Crimepoint.objects.filter(crimecat=self.type).filter(pt__within=poly).count()
            
            # Normalise
            val = (crimes - min_x)/(max_x-min_x)
            
            scale = float(val - HEATMAP_MIN) / float(HEATMAP_MAX - HEATMAP_MIN)
            # scale all channels linearly between START_COLOR and END_COLOR
            h, s, l = [int(scale*(end-start) + start) for start, end in zip(GREEN, RED)]
    
            block_color = "hsl(%s, %s%%, %s%%)" % (h, s, l)
        else:
            block_color = NONE_COLOR
            
        if neighbourhoods:
            pil_draw.polygon(locs, fill=block_color, outline=BLACK)
        else:
            pil_draw.polygon(locs, fill=block_color)# """, outline=WHITE"""