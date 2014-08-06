import os

# Configuration file

dataDisk = "/home/anb/data/"
boundaries_file = dataDisk+"shapefiles/England_dt_2001/England_dt_2001_area.shp"
neighbourhoods = dataDisk+"shapefiles/England_med_soa_2001/england_med_soa_2001.shp"
convexhulls_dir = dataDisk+"polygons/convexhulls/"
postcodeDir = dataDisk+"shapefiles/postcodes/"
poly_dir = dataDisk+"polygons/"
greater_london_out_dir = poly_dir+"greater_london/"
lastUpdatedFile = os.getcwd()+"/police/utils/.lastupdated"
dataDir = dataDisk+"data/"
csvDir = dataDisk+"data/csv/"
statDir =dataDisk+"data/stat/"
filteredDir = csvDir+"filtered/"
police_user = 'ditej15'
police_pass = '128cce61fe88a7212d04cc05a3770a9d'
police_data_url = "http://policeuk-2.s3.amazonaws.com/frontend/crime-data/"

## {city : [police, population]}
allcities = {"Liverpool" : ["merseyside", 466400],
                 "Manchester" : ["greater-manchester", 503100],
                 "Leeds" : ["west-yorkshire", 751500],
                 "Birmingham" : ["west-midlands", 1073000],
                 "Coventry" : ["west-midlands", 318600],
                 "Nottingham UA" : ["nottinghamshire", 305700],
                 "Bristol, City of UA" : ["avon-and-somerset", 428200],
                 "Bath and North East Some" : ["avon-and-somerset", 176000],
                 "Plymouth UA" : ["devon-and-cornwall", 256400],
                 "Oxford" : ["thames-valley", 151900],
                 "Southampton UA" : ["hampshire", 236900],
                 "Brighton and Hove UA" : ["sussex", 273400],
                 "City of London" : ["city-of-london", 7400],
                 "Greater London" : ["metropolitan", 8173900]
                 }
    
greater_london = ["Kingston upon Thames",
                       "Croydon",
                       "Bromley",
                       "Hounslow",
                       "Ealing",
                       "Havering",
                       "Hillingdon",
                       "Harrow",
                       "Brent",
                       "Barnet",
                       "Lambeth",
                       "Southwark",
                       "Lewisham",
                       "Greenwich",
                       "Bexley",
                       "Enfield",
                       "Waltham Forest",
                       "Redbridge",
                       "Sutton",
                       "Richmond upon Thames",
                       "Merton",
                       "Wandsworth",
                       "Hammersmith and Fulham",
                       "Kensington and Chelsea",
                       "Westminster",
                       "Camden",
                       "Tower Hamlets",
                       "Islington",
                       "Hackney",
                       "Haringey",
                       "Newham",
                       "Barking and Dagenham"]

"""allpolice = ["merseyside", #Liverpool
                 "greater-manchester", #Manchester
                 "west-yorkshire", #Leeds
                 "west-midlands", #Birmingham
                 "west-midlands", #Coventry
                 "nottinghamshire", #Nottingham
                 "avon-and-somerset", #Bristol
                 "avon-and-somerset", #Bath
                 "devon-and-cornwall", #Plymouth
                 "thames-valley", #Oxford
                 "hampshire", #Southampton
                 "sussex", #Brighton
                 "city-of-london", #City of London
                 "metropolitan" #Greater London
                 ]"""

postcodes = ["b.shp",
                 "ba.shp",
                 "bn.shp",
                 "bs.shp",
                 "cv.shp",
                 "e.shp",
                 "ec.shp",
                 "l.shp",
                 "ls.shp",
                 "m.shp",
                 "n.shp",
                 "ng.shp",
                 "nw.shp",
                 "ox.shp",
                 "pl.shp",
                 "se.shp",
                 "so.shp",
                 "sw.shp",
                 "w.shp",
                 "wc.shp"
                 ]

crimetypes = ["Burglary",
                 "Anti-social behaviour",
                 "Robbery",
                 "Vehicle crime",
                 "Other crime",
                 "Shoplifting",
                 "Criminal damage and arson",
                 "Public disorder and weapons",
                 "Drugs",
                 "Other theft",
                 "Violent crime",
                 ]
