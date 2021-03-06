#!/usr/bin/env python

from de_id_functions import *
import sys

# Working for year of birth and number of forum posts
def findBinEndpoints(qry, maxbinsize):
    """
   Given a max bin size, findBinEndpoints finds the appropriate endpoints
   that will create the smallest bins that have at least maxbinsize members.
   Note that this only works for integer bins.
   Note that if bins, for example, should be [1893-1917, 1918-1928, 1929-1931, etc.]
   then the endpoints will be: [1892,1917,1928,1931] : in other words, the endpoints of each interval.
    """
    i=0
    runningtotal = 0
    binbreaks = [int(qry[0][0])-1]
    while i < len(qry)-1:
        runningtotal += qry[i][1]
        # if running total of bins exceeds bin size, add as endpoint and start again
        # only if the remaining buckets have enough to also create a bin
        if runningtotal >= maxbinsize and sum([x[1] for x in qry[i+1:]]) >= maxbinsize:
            try: toappend = int(qry[i][0])
            except: toappend = qry[i][0]
            binbreaks.append(toappend)
            runningtotal = 0
        # If remaining do not have enough to make a bin, then don't add this
        # as an endpoint and just finish up by adding the last endpoint.
        elif runningtotal >= maxbinsize and sum([x[1] for x in qry[i+1:]]) < maxbinsize:
            try: toappend = int(qry[len(qry)-1][0])
            except: toappend = qry[len(qry)-1][0]
            binbreaks.append(toappend)
            runningtotal = 0
            return binbreaks
        i = i+1
    try: toappend = int(qry[len(qry)-1][0])
    except: toappend = qry[len(qry)-1][0]
    binbreaks.append(toappend) # append max value as the last endpoint
    return binbreaks


# Creates a dictionary that maps each unique value onto a corresponding
# range that takes endpoints
def createConversionDict(cursor, tableName, varName, origVarName, endpoints):
    """
    This takes in a list of endpoints as generated by findBinEndpoints and then
    creates a dictionary whose keys take on the value of all unique values
    of a given column, and whose corresponding values are the bin that each
    of the unique values in the dataset should be mapped onto.
    """
    qry = selUnique(cursor, tableName, varName)
    numDict = {}  # dictionary of unique values of value and how many times each occurs
    for item in qry:
        try:
            numDict[int(item[0])] = item[1]
        except:
            numDict[item[0]] = item[1]
    keys_sorted = sorted(numDict)
    keys_num = keys_sorted[:]
    for j in keys_num:
        if type(j) != int:
            keys_sorted.pop(keys_sorted.index(j))
    bins = endpts
    minBin = min(keys_sorted)
    maxBin = max(keys_sorted)
    binMap = {}
    for i in range(1, len(bins)):
        # if bin of length 1
        if bins[i] == bins[i - 1] + 1:
            binMap[bins[i]] = str(bins[i])
        else:
            for num in range(bins[i - 1], bins[i] + 1):
                if num == bins[i - 1]:
                    continue
                binMap[num] = str(bins[i - 1] + 1) + "-" + str(bins[i])
    newNumDict = {}
    for item in numDict:
        if item in binMap.keys():
            newNumDict[unicode(item)] = binMap[item]
        else:
            newNumDict[unicode(item)] = str(item)
    return newNumDict


# Creates a SQL table with mappings from unique values to binned values
def dictToTable(c, bin_dict, origVarName):
    """
    This takes in the dictionary as outputted by createConversionDict and
    then 
    """
    # Convert dictionary into a list of lists, each representing a row
    dict_list = []
    for k, v in bin_dict.iteritems():
        dict_list.append([k, v])
    # Build conversion table for year of birth
    # Create table that contains conversion from original YoB values to their binned values
    # (if it doesn't already exist)
    try:
        c.execute(
            "CREATE TABLE " + origVarName + "_bins (orig_" + origVarName + " text, binned_" + origVarName + " text)")
    except:
        pass
    # Insert each item of the dictionary
    for item in dict_list:
        c.execute("INSERT INTO " + origVarName + "_bins VALUES (?,?)", item)

def main(dbname):
    c = dbOpen(dbname)
    table = 'source'
    global qry, endpts, year_conversion, nforumposts_conversion
    ########################################################
    # Create new column called "YoB2" that is a duplicate of the "YoB" column
    try:
        addColumn(c, table, "YoB2")
        varIndex(c, table, "YoB2")
        simpleUpdate(c, table, "YoB2", "NULL")
        c.execute("UPDATE " + table + " SET YoB2 = YoB")
        c.execute("UPDATE " + table + " SET YoB2 = 9999 WHERE (YoB2 = '")
    except:
        c.execute("UPDATE " + table + " SET YoB2 = YoB")
        c.execute("UPDATE " + table + " SET YoB2 = 9999 WHERE YoB2 = ''")

    # Bin year of birth
    qry = selUnique(c, table, 'YoB2')
    endpts = findBinEndpoints(qry, YoB_binsize)
    print endpts
    # Create dictionary that maps every unique value to a corresponding bin
    year_conversion = createConversionDict(c, table, "YoB2", "YoB", endpts)
    # Delete the 9999 key, which corresponds to a NA value
    del year_conversion['9999']
    # Map an NA value back to NA
    year_conversion['NA'] = 'NA'
    # Convert dictionary to table named YoB_bins
    dictToTable(c, year_conversion, "YoB")
    # Check that the table values are correct
    c.execute("SELECT * FROM YoB_bins")
    c.fetchall()
    ########################################################
    # Create new column called "nforum_posts2" that is a duplicate of the "nforum_posts" column
    try:
        addColumn(c, table, "nforum_posts2")
        varIndex(c, table, "nforum_posts2")
        simpleUpdate(c, table, "nforum_posts2", "NULL")
        c.execute("UPDATE " + table + " SET nforum_posts2 = nforum_posts")
    except:
        c.execute("UPDATE " + table + " SET nforum_posts2 = nforum_posts")

    # Bin year of birth
    qry = selUnique(c, table, 'nforum_posts2')
    qry = sorted(qry, key=lambda x: int(x[0]))
    endpts = findBinEndpoints(qry, nforum_post_binsize)
    # Create dictionary that maps every unique value to a corresponding bin
    nforumposts_conversion = createConversionDict(c, table, "nforum_posts2", "nforum_posts", endpts)
    # Convert dictionary to table named YoB_bins
    dictToTable(c, nforumposts_conversion, "nforum_posts")
    # Check that the table values are correct
    #c.execute("SELECT * FROM nforum_posts_bins")
    #c.fetchall()
    #c.execute('Pragma table_info(source)')
    #print c.fetchall()


if __name__ == '__main__':
    dbname = sys.argv[1]
    main(dbname)