from __future__ import division
from django.contrib.gis import geos
from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos.point import Point
from django.db.models.aggregates import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from police.models import Crimepoint, Convexhull, Neighbourhood, Statistics, \
    MapPoints
from police.utils import utilities
from police.utils.ShpParser import ShpParser
from scipy.stats.stats import pearsonr
import datetime
import json

# Not used
def tiles(request, layer_name, z, x, y, extension):
    return redirect("http://192.9.206.105:8080/"+layer_name+"/"+z+"/"+x+"/"+y+"."+extension)

def crime_list(request):
    """
    Obsolete. Should convert bbox to OSGB36 before querying
    """
    coords = request.GET['bbox'].split(',')

    bbox = Polygon.from_bbox(coords)
    
    crimes = Crimepoint.objects.filter(pt__within=bbox)
    
    geojson_dict = {
        "type": "FeatureCollection",
        "features": [crime_to_geojson(crime) for crime in crimes]
    }
    
    return HttpResponse(json.dumps(geojson_dict), content_type='application/json')

def crime_to_geojson(crime):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [crime.pt.x, crime.pt.y]
        },
        "properties": {
            "description": crime.crimecat
        },
        "id": crime.id,
    }
    
def sense_list(request):
    coords = request.GET['bbox'].split(',')
    
    shp = ShpParser(None)
    p1 = shp.convert_point_to_OSGB36(coords[0], coords[1])
    p2 = shp.convert_point_to_OSGB36(coords[2], coords[3])
    OSGB36coors = [p1[0], p1[1], p2[0], p2[1]]
    bbox = Polygon.from_bbox(OSGB36coors)
    
    senses = MapPoints.objects.all()
    
    geojson_dict = {
        "type": "FeatureCollection",
        "features": [sense_to_geojson(sense) for sense in senses]
    }
    
    return HttpResponse(json.dumps(geojson_dict), content_type='application/json')

def sense_to_geojson(sense):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(sense.lon), float(sense.lat)],
        },
        "properties": {
            "description": sense.description,
            "level": sense.level, 
        },
        "id":sense.id,
    }
    
def convexhull_list(request):
    polys = []
    
    try: # If bbox exists as a parameter
        # Temporarily ignoring the bbox and loading all convexhulls
        coords = request.GET['bbox'].split(',')
        coords = [coords[1], coords[0], coords[3], coords[2]]
        bbox = Polygon.from_bbox(coords)
#        polys = Convexhull.objects.filter(poly__intersects=bbox)
        polys = Convexhull.objects.all()
    except: # Otherwise
        print "Loading convexhulls by name"
        try: # If the area name exists as a parameter
            area = request.GET['area']
            polys = Convexhull.objects.filter(name=area)
        except:
            pass
    
    geojson_dict = {
        "type": "FeatureCollection",
        "features": [convexhull_to_geojson(poly) for poly in polys]
    }
    
    return HttpResponse(json.dumps(geojson_dict), content_type='application/json')

def convexhull_to_geojson(poly):
    """ Converting the points to lng/lat, to match the specifications
    of features http://geojson.org/geojson-spec.html#feature-objects
    """
    points = []
    for pt in poly.poly[0]:
        points.append([pt[1], pt[0]])
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [points]
        },
        "properties": {
            "name": poly.name,
            "type": "convexhull"
        },
        "id": poly.id
    }
    
'''
Returns a list of neighbourhoods contained in the bounding box.
Used for heatmap generation.
'''
def neighbourhood_list(request):
    coords = request.GET['bbox'].split(',')

    shp = ShpParser(None)
    p1 = shp.convert_point_to_OSGB36(float(coords[1]), float(coords[0]))
    p2 = shp.convert_point_to_OSGB36(float(coords[3]), float(coords[2]))

    bbox = Polygon.from_bbox(p1+p2)
    
    polys = Neighbourhood.objects.filter(poly__intersects=bbox)
    features = []
    # For all the polygons we've retrieved from the database (in OSGB36 format)
    for poly in polys:
        coords = []
        if poly.poly and isinstance(poly.poly, geos.MultiPolygon):
            for inside_poly in poly.poly:
                inside_poly = inside_poly.simplify(100)
                for pt_pair in inside_poly.coords:
                    for pt in pt_pair:
                        p = shp.convert_point_to_WGS84(pt[0], pt[1])
                        coords.append((p[1], p[0]))
        else:
            poly.poly = poly.poly.simplify(100)
            for pt_pair in poly.poly.coords:
                    for pt in pt_pair:
                        p = shp.convert_point_to_WGS84(pt[0], pt[1])
                        coords.append((p[1], p[0]))
                        
        features.append(neighbourhood_to_geojson(poly, coords))
    
    geojson_dict = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return HttpResponse(json.dumps(geojson_dict), content_type='application/json')

def neighbourhood_to_geojson(poly, coords):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [list(coords)]
        },
        "properties": {
            "name": poly.name,
            "type": "neighbourhood"
        },
        "id": poly.id
    }

'''
Returns a single neighbourhood either based on a lat/lng point or a name.
Used for the charts generation
'''
def neighbourhood(request):
    polys = []
    shp = ShpParser(None)
    
    try: # If lat, lng exist as parameters
        lat = request.GET['lat']
        lng = request.GET['lng']
        pt = shp.convert_point_to_OSGB36(lat, lng)
        point = Point(pt[0], pt[1], srid=27700)
        polys = Neighbourhood.objects.filter(poly__contains=point)
    except: # Otherwise
        try: # If the area name exists as a parameter
            area = request.GET['area']
            polys = Neighbourhood.objects.filter(name=area)
        except:
            pass
    
    if len(polys) > 1:
        print "Error: more than one polygons found."
    else:
        features = []
        for poly in polys:
            coords = []
            if poly.poly and isinstance(poly.poly, geos.MultiPolygon):
                for inside_poly in poly.poly:
                    inside_poly = inside_poly.simplify(100)
                    for pt_pair in inside_poly.coords:
                        for pt in pt_pair:
                            p = shp.convert_point_to_WGS84(pt[0], pt[1])
                            coords.append((p[1], p[0]))
            else:
                poly.poly = poly.poly.simplify(100)
                for pt_pair in poly.poly.coords:
                        for pt in pt_pair:
                            p = shp.convert_point_to_WGS84(pt[0], pt[1])
                            coords.append((p[1], p[0]))
                            
            features.append(neighbourhood_to_geojson(poly, coords))
            
        geojson_dict = {
            "type": "FeatureCollection",
            "features": features
        }
        return HttpResponse(json.dumps(geojson_dict), content_type='application/json')
    
'''
Used for the pie chart
'''
def crimes_by_type(request):
    area = request.GET['area']
    level = request.GET['level']
    print "Getting crimes for area:", area
    
    crimes = None
    normalisation_value = None
    
    # Before that date the data are obsolete (some categories are merged together)
    date = datetime.datetime.strptime("2011-09-01", '%Y-%m-%d').date()
    
    if level == "city":
        crimes = Crimepoint.objects.filter(neighbourhood__council__convexhull__name=area
                                           ).filter(month__gte=date).distinct(
                                           ).values("crimecat").annotate(Count("crimecat"))
        normalisation_value = Statistics.objects.filter(name=area+"_population").all()[0].stat
    elif level == "neighbourhood":
        crimes = Crimepoint.objects.filter(neighbourhood__name=area
                                       ).filter(month__gte=date).distinct(
                                       ).values("crimecat").annotate(Count("crimecat"))
    
    dict = [crimetype_to_json(crime, normalisation_value) for crime in crimes]
    
    return HttpResponse(json.dumps(dict), content_type='application/json')

def crimetype_to_json(crime, normalisation_value=None):
    count = int(crime['crimecat__count'])
    
    if normalisation_value is not None:
        count = float((count*1000)/normalisation_value)
    else:
        # we have a neighbourhood
        count = float((count*1000)/7200)
    
    return {
        "label": crime['crimecat'],
        "data": count
    }
    
'''
Used for the line chart
'''
def crimes_by_type_groupby_date(request):
    area = request.GET['area']
    level = request.GET['level']
    print "Getting crimes for city:", area
    
    crimes = None
    
    if level == "city":
        # All crimes by date, in the given city
        crimes = Crimepoint.objects.filter(neighbourhood__council__convexhull__name=area).distinct(
                                           ).values("crimecat", "month"
                                                    ).annotate(Count("month"))
    elif level == "neighbourhood":
        # All crimes by date, in the given city
        crimes = Crimepoint.objects.filter(neighbourhood__name=area).distinct(
                                           ).values("crimecat", "month"
                                                    ).annotate(Count("month"))
                                                
    dict = {}
    totals = {}
    minDate = None
    maxDate = None

    for c in crimes:
        cat = c['crimecat']
        month = c['month']
        count = c['month__count']
        
        if (minDate is None) or (maxDate is None):
            minDate = maxDate = month
        elif month < minDate:
            minDate = month
        elif month > maxDate:
            maxDate = month
        
        if cat not in dict:
            dict[cat] = {}

        dict[cat][str(month)] = count
        
        # Calculating the totals for each month
        if str(month) in totals:
            totals[str(month)] += count
        else:
            totals[str(month)] = count
        
    dict["minDate"] = str(minDate)
    dict["maxDate"] = str(maxDate)
    
    return HttpResponse(json.dumps(dict), content_type='application/json')

def get_values(dict):
    monthlist = dict.keys()
    monthlist.sort()
    
    month = datetime.datetime.strptime(monthlist[0], '%Y-%m-%d').date()
    end_month = datetime.datetime.strptime(monthlist[len(monthlist)-1], '%Y-%m-%d').date()
    counts = []
    
    while month <= end_month:
        if dict.has_key(str(month)):
            counts.append(dict[str(month)])
        else:
            counts.append(0)
        month = utilities.addMonths(month, 1)
        
    return counts

def correlations(request):
    area = request.GET['area']
    level = request.GET['level']
    print "Getting crimes for city:", area
    
    crimes = None
    
    # Before this date the data are obsolete (some categories are merged together)
    date = datetime.datetime.strptime("2011-09-01", '%Y-%m-%d').date()
    
    if level == "city":
        # All crimes by date, in the given city
        crimes = Crimepoint.objects.filter(neighbourhood__council__convexhull__name=area).distinct(
                                           ).filter(month__gte=date).values("crimecat", "month"
                                                    ).annotate(Count("month"))
    elif level == "neighbourhood":
        # All crimes by date, in the given city
        crimes = Crimepoint.objects.filter(neighbourhood__name=area).distinct(
                                           ).filter(month__gte=date).values("crimecat", "month"
                                                    ).annotate(Count("month"))
           
    dict = {}       
    totals = {}

    for c in crimes:
        cat = c['crimecat']
        month = c['month']
        count = c['month__count']
        
        if cat not in dict:
            dict[cat] = {}

        dict[cat][str(month)] = count
        
        # Calculating the totals for each month
        if str(month) in totals:
            totals[str(month)] += count
        else:
            totals[str(month)] = count
    
    crimes = dict
    
    matrix = {}
    
    for key, value in crimes.items():
        matrix[key] = {}

        countsA = get_values(crimes[key])
        
        for k, v in crimes.items():
            countsB = get_values(crimes[k])
            
            pr = "null"
            
            if len(countsA) != len(countsB):
                if len(countsA) < len(countsB):
                    padding = [0]*(len(countsB)-len(countsA))
                    countsA = countsA+padding
                else:
                    padding = [0]*(len(countsA)-len(countsB))
                    countsB = countsB+padding
                    
            pr = "{0:.3f}".format(pearsonr(countsA, countsB)[0])
            
            matrix[key][k] = pr
            
    return HttpResponse(json.dumps(matrix), content_type='application/json')
    
            