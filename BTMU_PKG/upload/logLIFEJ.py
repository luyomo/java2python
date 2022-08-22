from ..common.common import Common
import os
from datetime import datetime
from datetime import timedelta
#import numpy as np

class logLIFEJ(Common):
    def __init__(self, shareName):
        super().__init__(shareName)
        self.CON_KEY_ACCOUNT_ALL0 = "0000000"

    def execute(self):
        """
        1. List all files from LOG_LIFEJ_FOLDER
           ----------- Each file from LOG_LIFEJ_FOLDER
           ---- Only for files
           1.1 Get the process date and bank code from the file name
           1.2 Open the file
               ---------- Each line from the file
               1.2.1 Read the type from first byte
                 -> 1 Read the paydate/header bank/header branch/header account and push header [paydate, branch, account] to vector
                 -> 2 Read the bank code/branch/account/amount 
                      1.2.2.1 If the header bank+branch+account is same. Source and destination is same, move it to delete vector with error code
                      1.2.2.2 If the account is 0000000, move it to delete vector with error code
                 -> 8
               1.2.2 Move the summary to return vector
               1.2.3 Append delete row to return vector
            1.3 Write source bank code to FILE_MARK_BANKCODE
            1.4 Write the number of bank code to FILE_MARK_WAITING [1/8]
        INPUT:
          LOG_LIFEJ_FOLDER
          FILE_WATCH_READ_ENCODING
          FILE_MARK_BANKCODE:
        Question: What's the FILE_MARK_BANKCODE
        """
        vecRtn = []
        vecBankCodeFile = []
        
        configData = self.readConfig("BTMU/TgtFiles/jaytest/etc/config.yml")

        strLOGLIFEJUrl = configData["LOG_LIFEJ_FOLDER"]
        strEncoding = configData["FILE_WATCH_READ_ENCODING"]
        strFileMarkBankcode = configData["FILE_MARK_BANKCODE"]
        strFileMarkWaiting = configData["FILE_MARK_WAITING"]
			  #vecGLFile = []
        #vecRtnInfo = []

        #strGLPaymentUrl = configData['GL_PAYMENT_FOLDER']
        #strEncoding = configData['GL_PAYMENT_ENCODING']
        #strFileTo = configData['GL_PAYMENT_COPYTO']
        #strFileModified = configData['GL_PAYMENT_MODIFIED']
        strFileFormat = configData['FILE_FORMAT']

        fileFormatConfig  = self.readConfig(strFileFormat)
        #print(f"The config data is {configData}")

        #arrModifiedData = []
        files = self.listShareFile(strLOGLIFEJUrl)
        # ---------- Loop all the files from the AP directory
        for file in files:
            fileName = file['name']

            strProcessDate = datetime.today().strftime('%Y%m%d')
            print(f"current date is {strProcessDate}")
            #vecBankCodeFile

            strBankCode = fileName[0:2]
            print(f"The bank code is {strBankCode}")

            if strBankCode not in ["J1", "J3", "AC", "AP"]: continue
            
            vecDeleteRow = []
            # Parse the AP file
            parsedData = self.parseFile(strFileFormat, f"{strLOGLIFEJUrl}/{fileName}", strEncoding)
            print(f"The parsed data is <{parsedData}>")
            _header = {}
            _tail = {}
            for _line in parsedData:
              if _line['DataType'] == "1":
                vecBankCodeFile.append(f"{strProcessDate},{_line['Account']},{strBankCode},")
                _header = _line
              if _line['DataType'] == "8":
                vecRtn.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},SUM(LIFE/J),{_line['TotalAcount']},{_line['TotalAmount']},")
              if _line['DataType'] == "2":
                if _header['BankCode'] == _line['BankCode'] and \
                  _header['BranchCode'] == _line['BranchCode'] and \
                  _header['Account'] == _line['Account']:
                  vecDeleteRow.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},SAME ACCOUNT,1,{_line['Amount']},{self.getLineStr(fileFormatConfig, _line)},")
                if _header['Account'] == self.CON_KEY_ACCOUNT_ALL0:
                  vecDeleteRow.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},0000000 ACCOUNT,1,{_line['Amount']},{self.getLineStr(fileFormatConfig, _line)},")
        vecRtn.append(vecDeleteRow)
        print(f"file: {vecBankCodeFile}")

        self.txtFileWrite(vecBankCodeFile, strFileMarkBankcode, strEncoding)

        self.txtFileWrite([str(len(vecBankCodeFile))], strFileMarkWaiting, strEncoding)

        return vecRtn