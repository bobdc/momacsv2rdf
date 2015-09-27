# momacsv2rdf.py: convert
# https://github.com/MuseumofModernArt/collection/commits/master/Artworks.csv
# to RDF, splitting up values into atomic ones where those atomic ones
# may be useful.
# I used python 3 instead of 2 because of its better handling of Unicode.

# For each regex, I should check for non-blank values that didn't match

import csv
import sys
import re

# We could parse out the artistBio with one regex, but
# the use of two will be easier to maintain.
lifeDateRangeRegEx = re.compile('.* ((\d\d\d\d)(–(\d\d\d\d))?.*)?')
nationalityRegEx = re.compile('(\w+)(, born ([a-zA-Z]+))?')

# Following must account for these examples:
#1935
#1939-43
#1880-1910
workDateRangeRegEx = re.compile('(\d\d\d\d)(-(\d+))?')

# Next regex pull cm dimension from dimensions values like these:
#23 15/16 x 17 15/16" (60.8 x 45.6 cm)
# 5/8 x 36 1/2 x 1 1/2" (121 x 92.7 x 3.8 cm)
metricDimensionsRegex = re.compile('(\d+\.?\d*) x (\d+\.?\d*)( x (\d+\.?\d*))? cm')
# at least 4 non-space chars because we don't want strings like  "cm)":
dimensionsQualifierRegex = re.compile('([a-zA-z\.,\-\(\)\&\@\+:;]{4,}\s*)+')

def convertRow(row):
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
         
         if(momaNumber != "MoMANumber"): # if it's not the header row

              # Get birth and death year figures
              birthYear = ""
              deathYear = ""
              lifeDateMatches = lifeDateRangeRegEx.search(artistBio)
              if lifeDateMatches != None:
                  if lifeDateMatches.group(2) != None:
                     birthYear = lifeDateMatches.group(2)
                  if lifeDateMatches.group(4) != None:
                     deathYear = lifeDateMatches.group(4)
              #print("[" + birthYear + " " + deathYear + "]")

              # Get nationality values
              citizenshipCountry = ""
              birthCountry = ""
              nationalityMatches = nationalityRegEx.search(artistBio)
              if nationalityMatches != None:
                  if nationalityMatches.group(1) != None:
                     citizenshipCountry = nationalityMatches.group(1)
                  if nationalityMatches.group(3) != None:
                     birthCountry = nationalityMatches.group(3)
                  #print(citizenshipCountry + " " + birthCountry)

              # If only one value in "date", make it workFinishDate. If two, set them as
              # workStartDate and workFinishDate (and account for 2-digit finish date).
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
              #print(workStartDate + "---" + workFinishDate)

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

              print("[" + str(heightCm) + "," + str(widthCm) + "," + str(depthCm) + "]")
              ##print(type(widthCm))
              ##print(20.2 * 3.3)
              #area = (heightCm * widthCm)   # why doesn't this work?
              ##print(area)

              dimensionsQualifierMatches = dimensionsQualifierRegex.search(dimensions)
              if dimensionsQualifierMatches != None:
                  print("qualifier: " + dimensionsQualifierMatches.group(0))


#############################################

if (len(sys.argv) < 2):
    print("No filename provided as input.")
    sys.exit()
else:
    inputfile = sys.argv[1]
    
try:
   with open(inputfile,  encoding='utf-8') as f:
       reader = csv.reader(f)
       for row in reader:
           convertRow(row)
except FileNotFoundError as e:
    print("File " + inputfile + " not found.")

