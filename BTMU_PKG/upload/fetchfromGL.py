from ..common.common import Common
import os
from datetime import datetime
from datetime import timedelta
import logging


class fetchfromGL(Common):
    def __init__(self, configFile, storageConnectionStr, localDir):
        super().__init__(configFile, storageConnectionStr, localDir)
        logging.debug(f"The config file is {self.configFile}")

    def execute(self, strFromPayDate, strAPHistory):
        """
        1. Loop all the files from GL_PAYMENT_FOLDER
           ---------- each file from GL_PAYMENT_FOLDER ----------
           ---- Only loop today's files
           1.1 Get the pay date from first line
           1.2 Continue if the paydate is not the thisThisPayDate
           1.3 Add the row to new vector
        2. Exist if there is no rows
        3. Sort the vector
        4. Save the vector to GL_PAYMENT_FOLDER
        5. Return the vector

        INPUT: 
          GL_PAYMENT_FOLDER
          GL_PAYMENT_ENCODING
          GL_PAYMENT_COPYTO
        """
        vecGLFile = []
        vecRtnInfo = []

        configData = self.readConfig(self.configFile)

        strGLPaymentUrl = configData['GL_PAYMENT_FOLDER']
        strEncoding = configData['GL_PAYMENT_ENCODING']
        strFileTo = configData['GL_PAYMENT_COPYTO']
        strFileModified = configData['GL_PAYMENT_MODIFIED']
        strFileFormat = configData['FILE_FORMAT']
     
        print(f"The config data is {configData}")

        arrModifiedData = []
        files = self.listShareFile(strGLPaymentUrl)

        # ---------- Loop all the files from the AP directory
        for file in files:
            fileName = file['name']
            # Parse the AP file
            parsedData = self.parseFile(strFileFormat, f"{strGLPaymentUrl}/{fileName}", strEncoding)
            # self.__logger.debug(parsedData)
            baseFileName = os.path.basename(fileName)

            # Get the header and go to next if there is no header
            firstLine = list(filter(lambda p: p['DataType'] == "1", parsedData))
            if len(firstLine) == 0:
                continue

            # print(firstLine[0]['ProcessDate'])
            # Get the actual process date from MMDD to YYYYMMDD, exists if not exist. start date|-> n days
            strProcessDate = self.findYYYYMMDD(strFromPayDate, "31", firstLine[0]['ProcessDate'])
            # print(f"The process date is {strProcessDate}")

            # Go to next if the date does not belong to the proper range
            if strProcessDate == "":
                continue
            # print(f"The file name is {os.path.basename(fileName)}")
            # Exists if the file has been processed.
            # Todo: How to get the strAPHistory
            if baseFileName in strAPHistory:
                continue

            vecGLFile.append(baseFileName)

            arrModifiedData.append({"fileName": baseFileName, "data": parsedData})

            vecRtnInfo.append({"File": baseFileName, "PayDate": strProcessDate})

        print(f"the GLFile is {vecGLFile}")
        print(f"The return file is {vecRtnInfo}")
 
        if len(vecGLFile) == 0:
            return {"CurrentFiles": vecRtnInfo}

        # ---------- Copy the files to other directory
        for fileName in vecGLFile:
            self.copyShareFile(f"{strGLPaymentUrl}/{fileName}", f"{strFileTo}/{fileName}")

        print("-----------------------------------------")
        for toModifiedData in arrModifiedData:
            print(f"The raw data is {toModifiedData['fileName']}")
            print(f"The raw data is {toModifiedData['data']}")
            for _row in toModifiedData['data']:
                print(f"The data to be convert {_row}")
                if _row['DataType'] == "2":
                    _row['Cust01Code'] = self.HenkanZenkaku(_row['Cust01Code'], strEncoding)
                # print(f"The file to be convert {_row['fileName']}")
                # print(f"The data to be convert {_row['data']}")
        print(f"The modified data is {arrModifiedData}")
        self.uploadData(strFileFormat, toModifiedData['data'], f"{strFileModified}/{toModifiedData['fileName']}", strEncoding)

        return {"CurrentFiles": vecRtnInfo}
