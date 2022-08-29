from ..common.common import Common
import os, logging
from datetime import datetime
from datetime import timedelta
import pyodbc
#import numpy as np

class readRowLIFEJ(Common):
    def __init__(self, configFile, storageConnectionStr, localDir):
      super().__init__(configFile, storageConnectionStr, localDir)
      print(f"The config file is {self.configFile}")
        
    def execute(self):
        """
        1. Read LIGE/J contents
        2. Loop LOG_LIFEJ_FOLDER
           ---------- Only loop files
           2.1 Get the calendar current date
           2.2 Get the bank code from file name
           2.3 Open the file
               ---------- Loop each lines
               2.3.1 Read the first byte
                 -> 1
                   | 2.3.1.1 Get the header pay date/ bank code/ branch code/ account
                   | 2.3.1.2 Push the detail to vecNewFile vector
                   | 2.3.1.3 Get the CUST CODE/CUST NAME/BANK CODE/BANK NAME from config file
                   |         CUSTCODE_J1: 123456789
                   |         CUSTNAME_J1: xxxxxxxxx
                   |         BANKCODE_J1: 0001
                   |         BANKNAME_J1: xxxxxx
                   | 2.3.1.4 Build the new header and push to new file vector
                 -> 2
                   | 2.3.2.1 Get the bank code/branch/account/amount
                   | 2.3.2.2 If the source and destination of bank/branch/account are same, push it to SameAccount list
                   | 2.3.2.3 If the account is 0000000, push it to ALL0 list
                   | 2.3.2.4. If othe case, calculate the amount and count of all the valid row for DB and file
                   | 2.3.2.4 Push to new file vector
                 -> 8 do nothing. Continue
                 -> 9 do nothing. Continue
               2.3.2 Push the data to return vector

          3. Push the summary record to vecRtn(DB)
          4. Push the summary record to new file
          5. Push the last row to vecRtn(DB)
          6. Push the last row to new file
          7. Write the new file
          8. If there is sameAccount rows, write out the records to LOG_FOLDER
          9. If there is All0 rows, write out the records to LOG_FOLDER
          10. Write the FILE_FIVE_ACCOUNT
          11. Prepare the data for email of All0
          12. Prepare the data for email of SameAccount
          13. Put the data for DB to mpRtn
          14. Put the email data to mpRtn

        INPUT:
          LOG_LOFEJ_FOLDER
          FILE_WATCH_READ_ENCODING
        OUTPUT:
          DB - Return vector
          New File
          Same Account Delete file
          All0 Delete file

        FUNC01: 
          INPUT: LIFEJ file
          OUTPUT: bank code file
        FUNC02:
          INPUT: LIFEJ file
          OUTPUT: SAME ACCOUNT/All0 Account/Summary
        FUNC02:
          INPUT: LEFEJ
          OUTPUT: 
        FUNC03:
          INPUT: LIFEJ
          OUTPUT: processdate,bankcode,rowdata,type
          Example:
            new header(replace bank code)
        FUNC04:
          INPUT: LIFEJ
          OUTPUT: New LIFEJ (Filter out the All0 and Same Account and calculate all again)
        FUNC05  
          "MAIL_ALL0": vecAll0Sort,
        FUNC06:
          "MAIL_SAMEACC" : vecSameAccSort
        """
        vecRtn = []
        vecTransRow = []
        vecTransLog = []
        vecFileAccounts = []
        arrNewFiles = []
        arrDeleted = []
        mpAll0 = {}
        mpSameAccount = {}
		    
        configData = self.readConfig(self.configFile)

        strLIFEJUrl = configData["LOG_LIFEJ_FOLDER"]
        strEncoding = configData["FILE_WATCH_READ_ENCODING"]
        strFileMarkBankcode = configData["FILE_MARK_BANKCODE"]
        strFileMarkWaiting = configData["FILE_MARK_WAITING"]
        
        # This is the file format from GL
        strFileFormat = configData['FILE_FORMAT']
        fileFormatConfig  = self.readConfig(strFileFormat)
        
        # Get the current date as the process date
        strProcessDate = datetime.today().strftime('%Y%m%d')
        logging.debug(f"Current date(process date) : {strProcessDate}")
        
        vecDeleteRow = []
        vecBankCodeFile = [] # Used to keep the data to output it file

        files = self.listShareFile(strLIFEJUrl)
        # ---------- Loop all the files from the AP directory
        for file in files:
            vecNewFile = []         # Keep the data for new file(Remove the ALL0 and SameAccount and re-sum the data)
            vecSameAccount = []     # Keep the same account data to output to file
            vecALL0Account = []     # Keep the all0 data to putput to file

            fileName = file['name'] # File name

            # To remove since it has been got from the main branch
            #strProcessDate = datetime.today().strftime('%Y%m%d')
            #print(f"current date is {strProcessDate}")
            #vecBankCodeFile

            lngSumAmount  = 0       # New sum account for new file(Remove All0 and Same account data)
            lngSumCount   = 0       # Same to lngSumAmount
            
            strBankCode = fileName[0:2]      # Get the bank code: J1/J3/AC/Ap
            print(f"The bank code is {strBankCode}")

            # Skip if the bank code is not in the list
            if strBankCode not in ["J1", "J3", "AC", "AP"]: continue

            # Todo: Skip if the file is directory.


            # Parse the AP file
            parsedData = self.parseFile(strFileFormat, f"{strLIFEJUrl}/{fileName}", strEncoding)
            logging.debug(f"Parsed data: <{parsedData}>")

            _header = {}         # Keep the header to get the meta data and same account judgement
            #_tail = {}
            for _line in parsedData:
              strRowType = ""                 # New data type
              if _line['DataType'] == "1":
                strRowType = "1"

                # Keep the data for new file.
                vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

                # Keep the data for five file mark
                vecBankCodeFile.append(f"{strProcessDate},{_line['Account']},{strBankCode},")
                
                # Replace the cust code/cust name/bank code/bank name in the header from the config file.
                # This information will be outputed to DB(Not output this replacement to new file)
                if strBankCode in configData['CUST_BANK_INFO']:
                  _line['CustCode'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['CustCode'], fileFormatConfig['Header']['CustCode'])
                  _line['CustName'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['CustName'], fileFormatConfig['Header']['CustName'])
                  _line['BankCode'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['BankCode'], fileFormatConfig['Header']['BankCode'])
                  _line['BankName'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['BankName'], fileFormatConfig['Header']['BankName'])
                _header = _line

              if _line['DataType'] == "2":

                # If the transfer account code is same to destination
                # 1. Output the data into file
                # 2. Output the data to trans_log to show the invalid data
                # 3. Remove it from the new file.
                if _header['BankCode'] == _line['BankCode'] and \
                  _header['BranchCode'] == _line['BranchCode'] and \
                  _header['Account'] == _line['Account']:
                  strRowType = "SAMEACC"
                  vecSameAccount.append(self.getLineStr(fileFormatConfig, _line))
                  mpSameAccount[fileName] = fileName

                  vecDeleteRow.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},SAME ACCOUNT,1,{_line['Amount']},{self.getLineStr(fileFormatConfig, _line)},")
                  vecTransLog.append({"process_date": strProcessDate, "bank_code": strBankCode, "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']), "record_type": "SAME ACCOUNT", "row_count": 1, "row_amount": _line['Amount'], "row_detail": self.getLineStr(fileFormatConfig, _line)})
                # If the accout is 0000000
                elif _line['Account'] == "0000000":
                  # 1. Output the data into file
                  # 2. Output the data to trans_log to show the invalid data
                  # 3. Remove it from the new file.
                  strRowType = "ALL0"
                  vecALL0Account.append(self.getLineStr(fileFormatConfig, _line))
                  mpAll0[fileName] = fileName

                  vecDeleteRow.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},0000000 ACCOUNT,1,{_line['Amount']},{self.getLineStr(fileFormatConfig, _line)},")
                  vecTransLog.append({"process_date": strProcessDate, "bank_code": strBankCode, "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']), "record_type": "0000000 ACCOUNT", "row_count": 1, "row_amount": _line['Amount'], "row_detail": self.getLineStr(fileFormatConfig, _line)})
                # General case
                else:
                  strRowType = "2"
                  vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

                  # Calculate the new sum and count for the new file
                  lngSumAmount  = lngSumAmount + int(_line['Amount'])
                  lngSumCount += 1

                # Keep the data to output the data to file
                vecRtn.append(f",{strProcessDate},{strBankCode},{_header['ProcessDate']},{self.getLineStr(fileFormatConfig, _line)},{strRowType},")
                # Todo : replace start date
                # Keep the data to insert it into dxc.trans_row 
                vecTransRow.append({"process_date": strProcessDate, "bank_code": _line['BankCode'], "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']), "row_detail": self.getLineStr(fileFormatConfig, _line), "row_type": strRowType})

              if _line['DataType'] == "8":
                # Prepare the new tail record with new amount and count
                _line['TotalAcount'] = self.LeftPadZero(lngSumCount, fileFormatConfig['Tail']['TotalAcount'])
                _line['TotalAmount'] = self.LeftPadZero(lngSumAmount, fileFormatConfig['Tail']['TotalAmount'])
                vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

              if _line['DataType'] == "9":
                # Nothing but output the data to new file.
                vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

            # If there is same account and all0 account, overwrite the file. 
            # Otherwise skip it.
            if len(vecDeleteRow) > 0:
              self.txtFileWrite(vecNewFile, f"{strLIFEJUrl}/{fileName}", strEncoding)
            
            retTimestamp =self.getLastModifiedTimestamp(f"{strLIFEJUrl}/{fileName}")
            #arrNewFiles.append({"FileName": f"{strLIFEJUrl}/{fileName}", "LastModifiedDate": retTimestamp})
            arrNewFiles.append(f"{strBankCode}<{fileName}>Last modified date-time:{retTimestamp}")
            
            # Output the same account data to file if exists
            if len(vecSameAccount) > 0:
              _fileName = self.GetFileNameWithTS(configData['FILE_SAME_ACCOUNT_NAME_PATTERN'], strBankCode)
              self.txtFileWrite(vecSameAccount, f"{configData['LOG_FOLDER_BACKUP']}/{_fileName}", strEncoding)
              arrDeleted.append(f"{_fileName}(All 0 Bank Accounts found and deleted, Total amount was summarized again.)")

            # Output ALL0 account data to file if exists
            if len(vecALL0Account) > 0:
              _fileName = self.GetFileNameWithTS(configData['FILE_ALL0_ACCOUNT_NAME_PATTERN'], strBankCode)
              self.txtFileWrite(vecALL0Account, f"{configData['LOG_FOLDER_BACKUP']}/{_fileName}", strEncoding)
              arrDeleted.append(f"{_fileName}(Same Bank Accounts found and deleted, Total amount was summarized again.")
        
            # Prepare the data for FILE_FIVE_MARKFILE
            vecFileAccounts.append(f"{strBankCode},{strProcessDate},{self.getFiveAccounts(parsedData)}")

        # Output the FILE_FIVE_ACCOUNT
        self.txtFileWrite(vecFileAccounts, f"{configData['FILE_FIVE_ACCOUNT']}", strEncoding)

        # The data for mail
        vecAll0Sort = self.sortFile(mpAll0)

        # The data for mail
        vecSameAccSort = self.sortFile(mpSameAccount)

        self.txtFileWrite(vecBankCodeFile, strFileMarkBankcode, strEncoding)

        self.txtFileWrite([str(len(vecBankCodeFile))], strFileMarkWaiting, strEncoding)

        # Insert the data into trans_row
        self.insertTransRow(vecTransRow)

        # Insert the data into trans_log
        self.insertTransLog(vecTransLog)

        return {
          "Email": {
            "LastModification": arrNewFiles,
            "InvalidSummary": arrDeleted
          }
        }

        return vecRtn

    def makeNewLIFEJFile(self):
      """ Filter out the SameAccount and All0 to make new LIFEJ file and summay
      """
      configData = self.readConfig(self.configFile)
      strFileFormat = configData['FILE_FORMAT']

      fileFormatConfig  = self.readConfig(strFileFormat)
      
      vecNewFile = []
      lngSumAmount  = 0
      lngSumCount   = 0
      
      def funcHeader(_fileName, _bankCode, _line, _strLine):
        print(f"Header handling")
        vecNewFile.append(_strLine)

      def funcBody(_fileName, _bankCode, _line, _strLine):
        print(f"body  handling")
        vecNewFile.append(_strLine)
        lngSumAmount  = lngSumAmount + int(_line['Amount'])
        lngSumCount += 1

      def funcBodySameAccount(_fileName, _bankCode, _line, _strLine):
        print(f"body - Same account handling")

      def funcBodyAll0(_fileName, _bankCode, _line, _strLine):
        print(f"body - All0  handling")

      def funcBodySameAccount(_fileName, _bankCode, _line, _strLine):
        print(f"body - same account  handling")

      def funcBodyAll0(_fileName, _bankCode, _line, _strLine):
        print(f"body - 000000  handling")

      def funcTail(_fileName, _bankCode, _line, _strLine):
        print(f"Tail handling")
        _line['TotalAcount'] = self.LeftPadZero(lngSumCount, fileFormatConfig['Tail']['TotalAcount'])
        _line['TotalAmount'] = self.LeftPadZero(lngSumAmount, fileFormatConfig['Tail']['TotalAmount'])
        vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

      def funcEnd(_fileName, _bankCode, _line, _strLine):
        print(f"End handling")
        vecNewFile.append(_strLine)

      self.loopLifeJ(funcHeader, funcBody, funcBodySameAccount, funcBodyAll0, funcTail, funcEnd )

      print(f"The processed data is {vecNewFile}")

    def loopLifeJ(self, _funcHeader, _funcBody, _funcBodySameAccount, _funcBodyAll0, _funcTail, _funcEnd):
      configData = self.readConfig(self.configFile)
      strLIFEJUrl = configData["LOG_LIFEJ_FOLDER"]
      strEncoding = configData["FILE_WATCH_READ_ENCODING"]
      strFileFormat = configData['FILE_FORMAT']

      fileFormatConfig  = self.readConfig(strFileFormat)
      
      files = self.listShareFile(strLIFEJUrl)

      for file in files:
        fileName = file['name']
        print(f"The file is {fileName}")

        strBankCode = fileName[0:2]
        print(f"The bank code is {strBankCode}")

        if strBankCode not in ["J1", "J3", "AC", "AP"]: continue

        print(f"The file to open is {strLIFEJUrl}/{fileName}")
         
        parsedData = self.parseFile(strFileFormat, f"{strLIFEJUrl}/{fileName}", strEncoding)
        
        _header = {}
        print(f"The parsed data is <{parsedData}>")
        for _line in parsedData:
          if _line['DataType'] == "1":
            _header = _line
            _funcHeader(fileName, strBankCode, _line, self.getLineStr(fileFormatConfig, _line))
            
          if _line['DataType'] == "2":
            if _header['BankCode'] == _line['BankCode'] and \
                  _header['BranchCode'] == _line['BranchCode'] and \
                  _header['Account'] == _line['Account']:
              _funcBodySameAccount(fileName, strBankCode, _line, self.getLineStr(fileFormatConfig, _line))
            elif _header['Account'] == "0000000":
              _funcBodyAll0(fileName, strBankCode, _line, self.getLineStr(fileFormatConfig, _line))
            else:
              _funcBody(fileName, strBankCode, _line, self.getLineStr(fileFormatConfig, _line))

          if _line['DataType'] == "8":
            _funcTail(fileName, strBankCode, _line, self.getLineStr(fileFormatConfig, _line))

          if _line['DataType'] == "9":
            _funcEnd(fileName, strBankCode, _line, self.getLineStr(fileFormatConfig, _line))


    def getFiveAccounts(self, parsedData):
      idx = 0
      strRet = ""
      for _line in parsedData:
        if _line['DataType'] != "2": continue
        idx += 1
        if idx <=5: strRet += f",{_line['Account']}|{_line['Amount']}"
      return strRet

    def sortFile(self, inArr):
      """ Sort the content as J1->J3->AC->AP

      Args:
          inArr (_type_): Input string
      Output:
          Sorted array of string
      """
      return dict(sorted(inArr.items(), key=lambda item: f"{item[1][1:2]}{item[1]}")).values()
      
    def fetchLatestRunNum(self):
      def dbExecute(cursor):
        cursor.execute("select 1")
        row = cursor.fetchone()
        logging.info(f"The result inside dbExecute is {row}")
        return row if row else 0
      ret = self.executeDB(dbExecute)
      logging.info(f"The result after executeDB is {ret}")

    def insertTransRow(self, _data):
      def dbExecute(cursor):
        try:
          for _idx, _line in enumerate(_data):
            __query = f"insert into dxc.transbiz_row values('{_line['process_date']}', {_idx + 1} , '{_line['bank_code']}', '{_line['pay_date']}', N'{_line['row_detail']}', '{_line['row_type']}', current_timestamp, current_user)"
            logging.info(f"the query is {__query}")
            cursor.execute(__query)
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            logging.info(f"Failed on the db: {sqlstate}")
        
      ret = self.executeDB(dbExecute)
      logging.info(f"The result after executeDB is {ret}")

    def insertTransLog(self, _data):
      def dbExecute(cursor):
        try:
          for _idx, _line in enumerate(_data):
            __query = f"insert into dxc.transbiz_log values('{_line['process_date']}', {_idx + 1} , '{_line['bank_code']}', '{_line['pay_date']}', '{_line['record_type']}', {_line['row_count']}, {_line['row_amount']}, N'{_line['row_detail']}', current_timestamp, current_user)"
            logging.info(f"the query is {__query}")
            cursor.execute(__query)
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            logging.info(f"Failed on the db: {sqlstate}")
        
      ret = self.executeDB(dbExecute)
      logging.info(f"The result after executeDB is {ret}")



        