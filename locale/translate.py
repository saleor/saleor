import sys
import os.path
import re

# Run once to extrac all missing msgstr
# Translate missing ones, save file under different name(!!!)
# Run skript again to insert all translated strings, after this the todo file will be overwritten

def main():
# Define all needed Paths
    orgPath = ".\LC_MESSAGES\django.po"
    savePath = "new_django.po"
    ToDoPath = "ToDo.txt"

# Open File, intialize strings
    orgFile = open(str(orgPath), "rb")
    orgString =  str(orgFile.read().decode("UTF-8"))

    saveFile = open(str(savePath), "wb")
    saveString = orgString

    if os.path.exists(ToDoPath):
        ToDoFile = open(str(ToDoPath), "rb")
        ToDoString =  str(ToDoFile.read().decode("UTF-8"))
        ToDoFile.close()
        ToDoFile = open(str(ToDoPath), "wb")
        
    else:
        ToDoFile = open(str(ToDoPath), "wb")
        ToDoString = ""
    
# Make array of tupels with all ids and strings
# note that the complete multiline ids and strings are only in stringIDArray[i][0] and [i][3]
# because I can't handle re apparently 
    stringIDArray = re.findall(r'msgid ((".*"\s?)*)\nmsgstr ((".*"?\s)*)' , ToDoString, re.MULTILINE)

# Remove all empty msgstr so that those IDs show up in the ToDo file later

    for i in range(0, len(stringIDArray)):
        strid = 'msgid ' + stringIDArray[i][0]
        strmsg = strid + '\nmsgstr ' + stringIDArray[i][3] 

# if msgid == "", we don't need it and it could screw things up
# if strid not in SaveString, means this string is not used 
        if stringIDArray[i][3] != '""' and stringIDArray[i][3] is not None:
            saveString = saveString.replace(strid, strmsg)
            print(strid + " \nreplaced with \n" + strmsg)

    saveString = re.sub(r'msgstr (".*"?\s)*msgstr ""\n*', '', saveString)
# finds all msgid without corresponding msgstr      
    notFoundStrings = re.findall(r'msgid ((".*"\s?)*)\nmsgstr ""\s*#' , saveString, re.MULTILINE)
    ToDoString = ""
# makes easy to work with ToDo file
    for i in range(0, len(notFoundStrings)):
        ToDoString += 'msgid ' + notFoundStrings[i][0] +  'msgstr "" \n\n'

# close and write all files
    orgFile.close()
    saveFile.write(saveString.encode("UTF-8"))
    saveFile.close()
    ToDoFile.write(ToDoString.encode("UTF-8"))
    ToDoFile.close()

if __name__=="__main__":
    main()
