# -*- coding: utf-8 -*-
import pandas as pd
import csv
import writeCSV
import requests
from tabulate import tabulate
from time import sleep
import sys

# Print iterations progress
def printProgress(iteration, total, prefix='', suffix='', decimals=1, bar_length=50):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

#create csv file for testing
def makeTest():
    deletefile = open("test.csv", "w")
    deletefile.close()
    f1 = open("test.csv", "a")
    test = csv.writer(f1, dialect = 'excel')
    test.writerow(["Ticker", "Name"])
    test.writerow(["FCCY", "Something"])
    test.writerow(["HPE$", "Something else"])
    f1.close()

#add EPS and growth rate to the csv
def addEPSandGrowthRateToCSV():
    f1 = open("tickers.csv", "a+")
    tickers = pd.read_csv(f1)
    epsToAdd = []
    currentPriceToAdd = []
    targetPriceToAdd = []
    #used for primitive loading bar
    numRows = tickers.shape[0]
    i = 0
    printProgress(i, numRows, prefix = "Progress:", suffix = "Complete")
    for row in tickers.iterrows():
        #querys each ticker individually - probably more efficient to group by 200 -fix later
        url =  "http://download.finance.yahoo.com/d/quotes.csv?"
        #get ticker in non-index column
        if ("$" in row[1]["Ticker"]):
            epsToAdd.append("N/A")
            currentPriceToAdd.append("N/A")
            targetPriceToAdd.append("N/A")
            continue
        url += "s=" + row[1]["Ticker"]
        url += "&f=e7l1t8"
        with requests.Session() as s:
            #downloads csv with columns of eps, current price, and targetPrice 1 year from time of request
            #setup to avoid connection errors
            downloadDone = False
            #counter to detect when network errors should stop the program - I have decided that after five attempts
            #to connect an error should stop the program
            connectionCounter = 0
            while not downloadDone:
                if connectionCounter <= 5:
                    try:
                        download = s.get(url)
                        downloadDone = True
                    except:
                        print("\nConnection refused by the server..")
                        print("The connection will be attempted again in 5 seconds")
                        sleep(5)
                        connectionCounter += 1
                        continue
                else:
                    download = s.get(url)
                    downloadDone =True
            #decodes csv
            decoded_content = download.content.decode('utf-8')
            stockInfo = csv.reader(decoded_content.splitlines(), delimiter = ",")
            for stockRow in stockInfo:
                first = True
                second = True
                for stockCol in stockRow:
                    if first:
                        epsToAdd.append(stockCol)
                        first = False
                    elif second:
                        currentPriceToAdd.append(stockCol)
                        second = False
                    else:
                        targetPriceToAdd.append(stockCol)
        #update progress bar
        sleep(0.1)
        i+=1
        printProgress(i, numRows, prefix = "Progress:", suffix = "Complete")
        
    tickers = tickers.assign(EPS = epsToAdd)
    tickers = tickers.assign(CurrentPrice = currentPriceToAdd)
    tickers = tickers.assign(TargetPrice = targetPriceToAdd)
    #drop rows with bad data
    tickers.dropna(how = 'any', inplace = True)
    tickers.to_csv("tickers.csv", index = False)
    f1.close()


#removes nan and N/A rows in the data - needed b/c other call doesnt work for some reason
def removeBadData():
    f1 = open("tickers.csv", "a+")
    tickers = pd.read_csv(f1)
    tickers.dropna(how = 'any', inplace = True)
    tickers.to_csv("tickers.csv", index = False)
    f1.close()

#calculates adds the growth rate to the csv
def addGrowthRate():
    f1 = open("tickers.csv", "a+")
    tickers = pd.read_csv(f1)
    tickers = tickers.assign(EstimatedGrowthRate =((tickers['TargetPrice'] - tickers['CurrentPrice']) / tickers['CurrentPrice']) * 100)
    tickers.to_csv("tickers.csv", index = False)
    f1.close()

#adds the graham numbers to the csv
def addGrahamEstimateOfValue():
    #generates the intrinsic value of a stock via the Benjamin
    #Graham formula V =  (EPS * (8.5 + 2g) * 4.4) / Y where g is the estimated growth rate
    #and Y is the current yield on a 20 year AAA corporate bond
    f1 = open("tickers.csv", "a+")
    #taken from moody's seasoned aaa corporate bond yield on jun 28 2017
    bondRate = 3.66
    tickers = pd.read_csv(f1)
    tickers = tickers.assign(IntrinsicValue = (tickers['EPS'] *(8.5 + 2*tickers['EstimatedGrowthRate']) * 4.4) / bondRate)
    #then compare valuation of stock with actual price
    tickers = tickers.assign(RelativeGrahamValue = tickers['IntrinsicValue'] / tickers['CurrentPrice'])
    tickers.to_csv("tickers.csv", index = False)
    f1.close()

#orders csv with highest graham numbers first
def orderAndDisplayData():
    #displays data with the highest relative graham value first
    f1 = open("tickers.csv", "a+")
    tickers = pd.read_csv(f1)
    tickers = tickers.sort_values(['RelativeGrahamValue'], ascending = False)
    #prints highest value 100 stocks
    print(tickers.head(100))
    #then prints lowest value 50 stocks
    print(tickers.tail(50))
    #save sorted csv
    tickers.to_csv("tickers.csv", index = False)
    f1.close()

if __name__ == "__main__":
    writeCSV.updateTickers()
    writeCSV.fixCSV()
    addEPSandGrowthRateToCSV()
    addGrowthRate()
    addGrahamEstimateOfValue()
    removeBadData()
    orderAndDisplayData()
