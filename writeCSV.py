import requests
import csv
import pandas as pd

def fixCSV():
    #removes unnecessary and non-uniform information
    tickers = pd.read_csv("tickers.csv", header = None)
    tickers = tickers[[0, 1]]
    tickers.to_csv("tickers.csv", index = False)
    #couldnt do in above variable b/c pandas no longer recongnized the 0, 1 index call
    addColumnNames = pd.read_csv("tickers.csv", header = None, names = ["Ticker", "Name"])
    #get rid of duplicates and a useless row that appears for some reason
    addColumnNames = addColumnNames.drop_duplicates()
    addColumnNames.drop(0, inplace = True)
    #gets rid of name column due to weird issues with writing to csv
    addColumnNames = addColumnNames["Ticker"]
    addColumnNames.to_csv("tickers.csv", index = False)
    #finally - read Tickers column label
    finalFix = pd.read_csv("tickers.csv", header = None,  names = ["Ticker"])
    finalFix.to_csv("tickers.csv", index = False)

def updateTickers():
    #delete previous file
    deletefile = open("tickers.csv", "w")
    deletefile.close()
    #file to store tickers in
    tickers = open("tickers.csv", "a")
    tickerscsv = csv.writer(tickers, dialect='excel')
    #csv locations for tickers
    nasdaq = "http://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=NASDAQ&render=download"
    nyse = "http://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=NYSE&render=download"
    urlList = [nasdaq, nyse]
    for url in urlList:
        #keeps connection to improve performance
        with requests.Session() as s:
            #downloads csv
            download = s.get(url)
            #splits csv into lines
            decoded_content = download.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter = ",")
            firstLine = True
            for lines in cr:
                #skips the first line of every file
                if firstLine:
                    firstLine = False
                    continue
                else:
                    tickerscsv.writerow(lines)
           
    #close tickers file
    tickers.close()

if __name__ == "__main__":
    updateTickers()
    fixCSV()
