# momacsv2rdf.py: convert
# https://github.com/MuseumofModernArt/collection/commits/master/Artworks.csv
# to RDF, splitting up values into atomic ones where those atomic ones
# may be useful.
# I used python 3 instead of 2 because of its better handling of Unicode.
# If running with Windows, remember to SET PYTHONIOENCODING=utf_8

import csv
import sys
import re

##### regular expressions ######

extraSpaceRegEx = re.compile('^\s*(.+?)\s*$')
allDigitsRegEx = re.compile('^\d+$')

# We could parse out the artistBio with one regex,
# but the use of two will be easier to maintain.
lifeDateRangeRegEx = re.compile('.* ((\d\d\d\d)(–(\d\d\d\d))?.*)?')

# want to match this: (French and Swiss, born Switzerland 1944)
nationalityRegEx = re.compile('(\w+)( and (\w+))?(, born ([a-zA-Z]+))?')

# Following must account for examples 1935 1939-43 1880-1910
workDateRangeRegEx = re.compile('(\d\d\d\d)(-(\d+))?')

# Next regex pull cm dimension from dimensions values like these:
# 23 15/16 x 17 15/16" (60.8 x 45.6 cm)"
# 5/8 x 36 1/2 x 1 1/2" (121 x 92.7 x 3.8 cm)
metricDimensionsRegex = re.compile('(\d+\.?\d*) x (\d+\.?\d*)( x (\d+\.?\d*))? cm')

# Note in a dimensions statement such as "Each" or "unfolded." At
# least 4 non-space chars because we don't want strings like "cm)":
dimensionsNoteRegex = re.compile('([a-zA-z\.,\-\(\)\&\@\+:;]{4,}\s*)+')


############# function definitions ################


def printPredicateObjectIfObject(predicate,object,type):

    """ Print the predicate and object if the object isn't a blank
    string. Use type to determine whether object needs quotes or is boolean.
    """
    
    if object != "":

        if type == "boolean":
            if object == "Y":
                print("     " + predicate + " true ;")
            elif object == "N":
                print("     " + predicate + " false ;")
                
        elif type == "date":
            print("     " + predicate + ' "' + object + '"^^xsd:date ;')

        elif type == "numeric":
            print("     " + predicate + " " + str(object) + " ;")

        elif type == "URI":
            print("     " + predicate + " <" + object + "> ;")

        else:
            # Just treat it as a string. 
            extraSpaceMatches = extraSpaceRegEx.match(object)
            if extraSpaceMatches != None:   # Remove leading and trailing space.
                object = extraSpaceMatches.group(1)
            object = str.replace(object,"\n"," ")
            object = str.replace(object,"\\","\\\\")   # escape any backslashes
            object = str.replace(object,'"','\\"')   # escape any quotes
            print("     " + predicate + ' "' + object + '" ;')



def convertRow(row):
    """ Take the split-up row, use regexes to pull new
    pieces of information, and output triples for each fact.
    """
    title = row[0] 
    artist = row[1]
    artistBio = row[2]
    date = row[3]
    medium = row[4]
    dimensions = row[5]
    creditLine = row[6]
    momaNumber = row[7]
    classification = row[8]
    department = row[9]
    dateAcquired = row[10]
    curatorApproved = row[11]
    objectID = row[12]
    url = row[13]
    allDigitsMatches = allDigitsRegEx.match(objectID)
    if(momaNumber == "MoMANumber"):
        # It's the header row, so ignore
        pass
    elif allDigitsMatches == None:  # not a proper objectID
        print("# Error parsing the following input line ", end="")
        print("(13th value of \"" + objectID + "\" is not all digits):\n# ", end="")
        print(row, end="")
        print("\n")
    else:
         # Get birth and death year figures
         birthYear = ""
         deathYear = ""
         lifeDateMatches = lifeDateRangeRegEx.search(artistBio)
         if lifeDateMatches != None:
             if lifeDateMatches.group(2) != None:
                birthYear = lifeDateMatches.group(2)
             if lifeDateMatches.group(4) != None:
                deathYear = lifeDateMatches.group(4)

         # Get nationality values
         citizenshipCountry1 = ""
         citizenshipCountry2 = ""
         birthCountry = ""
         nationalityMatches = nationalityRegEx.search(artistBio)
         if nationalityMatches != None:  
             if nationalityMatches.group(1) != None:
                citizenshipCountry1 = nationalityMatches.group(1)
             if nationalityMatches.group(3) != None:
                citizenshipCountry2 = nationalityMatches.group(3)
             if nationalityMatches.group(5) != None:
                birthCountry = nationalityMatches.group(5)

         # If only one value in "date", make it
         # workFinishDate. If two, set them as workStartDate and
         # workFinishDate (and account for 2-digit finish date).
         workStartDate = ""
         workFinishDate = ""
         workDateMatches = workDateRangeRegEx.search(date)
         if workDateMatches != None:
             if workDateMatches.group(3) == None:
                workFinishDate = workDateMatches.group(1)
             else:
                workStartDate = workDateMatches.group(1)
                workFinishDate = workDateMatches.group(3)
                if len(workFinishDate) == 2:
                    workFinishDate = workStartDate[:2] + workFinishDate

         # Some use × for dimensions, so normalize
         heightCm = ""
         widthCm = ""
         depthCm = ""
         dimensions = str.replace(dimensions,"×","x")
         metricDimensionsMatches = metricDimensionsRegex.search(dimensions)
         if metricDimensionsMatches != None:
             # Based on the figures for Monet's "Water Lilies"
             # I'm assuming that it's Height x Width
             if metricDimensionsMatches.group(1) != None:
                heightCm = float(metricDimensionsMatches.group(1))
             if metricDimensionsMatches.group(2) != None:
                widthCm = float(metricDimensionsMatches.group(2))
             if metricDimensionsMatches.group(4) != None:
                depthCm = float(metricDimensionsMatches.group(4))

         dimensionsNote = ""
         dimensionsNoteMatches = dimensionsNoteRegex.search(dimensions)
         if dimensionsNoteMatches != None:
             dimensionsNote = dimensionsNoteMatches.group(0)

         # I'd use the url value as the identifier, but they don't all have one,
         # so when they do this adds an owl:sameAs triple.
         print("<http://rdfdata.org/models/moma/id/" + objectID + ">")
         printPredicateObjectIfObject("ci:P43_has_dimension",
                                      dimensions,"string")
         printPredicateObjectIfObject("rdfs:label",title,"string")
         printPredicateObjectIfObject("dc:creator",artist,"string")
         printPredicateObjectIfObject("rdaGr2:biographicalInformation",
                                      artistBio,"string")
         printPredicateObjectIfObject("dc:date",date,"string")
         printPredicateObjectIfObject("ci:P2_has_type",medium,"string")
         printPredicateObjectIfObject("ci:P43_has_dimension",
                                      dimensions,"string")
         printPredicateObjectIfObject("ci:P23_transferred_title_from",
                                      creditLine,"string")
         printPredicateObjectIfObject("ci:P48_has_preferred_identifier",
                                      momaNumber,"string")
         printPredicateObjectIfObject("m:classification",
                                      classification,"string")
         printPredicateObjectIfObject("m:department",department,"string")
         printPredicateObjectIfObject("m:dateAcquired",dateAcquired,"date")
         printPredicateObjectIfObject("m:curatorApproved",
                                      curatorApproved,"boolean")
         printPredicateObjectIfObject("dc:identifier",objectID,"string")
         printPredicateObjectIfObject("owl:sameAs",url,"URI")
         printPredicateObjectIfObject("m:widthCm",widthCm,"numeric")
         printPredicateObjectIfObject("m:heightCm",heightCm,"numeric")
         printPredicateObjectIfObject("m:depthCm",depthCm,"numeric")
         printPredicateObjectIfObject("m:dimensionsNote",
                                      dimensionsNote,"string")
         printPredicateObjectIfObject("rdaGr2:placeOfBirth",
                                      birthCountry,"string")
         printPredicateObjectIfObject("rdaGr2:countryAssociatedWithThePerson",
                                      citizenshipCountry1,"string")
         printPredicateObjectIfObject("rdaGr2:countryAssociatedWithThePerson",
                                      citizenshipCountry2,"string")
         printPredicateObjectIfObject("rdaGr2:dateOfBirth",birthYear,"numeric")
         printPredicateObjectIfObject("rdaGr2:dateOfDeath",deathYear,"numeric")
         printPredicateObjectIfObject("m:workStartDate",workStartDate,"numeric")
         printPredicateObjectIfObject("m:workFinishDate",
                                      workFinishDate,"numeric")

         print(".")

#############################################

if (len(sys.argv) < 2):
    print("No filename provided as input.")
    sys.exit()
else:
    inputfile = sys.argv[1]

try:
   with open(inputfile,  encoding='utf-8') as f:
       reader = csv.reader(f)
       print("# This data was generated by the Python script at")
       print("# https://github.com/bobdc/momacsv2rdf using CSV data from")
       print("# https://github.com/MuseumofModernArt/collection as input. This")
       print("# version may not be up to date with the latest data there.")
       print("# This dataset is placed in the public domain using a  CC0 License")
       print("# (https://creativecommons.org/publicdomain/zero/1.0/)\n")

       print("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
       print("@prefix ci: <http://www.cidoc-crm.org/cidoc-crm/> .")
       print("@prefix r: <http://rdvocab.info/ElementsGr2/> .")
       print("@prefix m: <http://rdfdata.org/models/moma/> .")
       print("@prefix dc: <http://purl.org/dc/elements/1.1/> .")
       print("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
       print("@prefix rdaGr2: <http://RDVocab.info/ElementsGr2/> .")
       print("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
       print("\n");
       for row in reader:
           convertRow(row)
           
except FileNotFoundError as e:
    print("File " + inputfile + " not found.")

