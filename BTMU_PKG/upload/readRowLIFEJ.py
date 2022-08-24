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
        mpRtn = {}
        vecRtn = []
        vecTransRow = []
        vecTransLog = []
        vecFileAccounts = []
        mpAll0 = {}
        mpSameAccount = {}
		    
        configData = self.readConfig(self.configFile)

        strLIFEJUrl = configData["LOG_LIFEJ_FOLDER"]
        strEncoding = configData["FILE_WATCH_READ_ENCODING"]
        strFileMarkBankcode = configData["FILE_MARK_BANKCODE"]
        strFileMarkWaiting = configData["FILE_MARK_WAITING"]
        
        #strFileMarkBankcode = configData["FILE_MARK_BANKCODE"]
        #strFileMarkWaiting = configData["FILE_MARK_WAITING"]
			  #vecGLFile = []
        #vecRtnInfo = []

        #strGLPaymentUrl = configData['GL_PAYMENT_FOLDER']
        #strEncoding = configData['GL_PAYMENT_ENCODING']
        #strFileTo = configData['GL_PAYMENT_COPYTO']
        #strFileModified = configData['GL_PAYMENT_MODIFIED']
        strFileFormat = configData['FILE_FORMAT']

        fileFormatConfig  = self.readConfig(strFileFormat)
        #print(f"The file config is <{fileFormatConfig}>")
        #print(f"The config data is {configData}")

        #test="1111"
        #print(f"The character beore conversion ->{test}<-")
        #test= self.RightPadSpace(test, fileFormatConfig['Header']['CustCode'])
        #print(f"The character beore conversion ->{test}<-")

        #test02=1111
        #print(f"The character beore conversion ->{test02}<-")
        #test02= self.LeftPadZero(test02, fileFormatConfig['Tail']['TotalAmount'])
        #print(f"The character beore conversion ->{test02}<-")

        
        #if 1==1 :
        #  return

        strProcessDate = datetime.today().strftime('%Y%m%d')
        print(f"current date is {strProcessDate}")

        #def _funcHeader(_line):
        #  pass

        #print("Hello new function")    
        #self.makeNewLIFEJFile()
        #self.loopLifeJ(self, strLIFEJUrl, _funcHeader, _funcBody, _funcTail, _funcEnd)
        
        #return 
        #arrModifiedData = []
        vecDeleteRow = []
        vecBankCodeFile = [] # Used to keep the data to output it file

        files = self.listShareFile(strLIFEJUrl)
        # ---------- Loop all the files from the AP directory
        for file in files:
            vecNewFile = []
            vecSameAccount = []
            vecALL0Account = []

            fileName = file['name']

            strProcessDate = datetime.today().strftime('%Y%m%d')
            print(f"current date is {strProcessDate}")
            #vecBankCodeFile

            lngSumAmount  = 0
            lngSumCount   = 0
            #lngFileSumAmount  = 0
            #lngFileSumCount   = 0

            strBankCode = fileName[0:2]
            print(f"The bank code is {strBankCode}")

            if strBankCode not in ["J1", "J3", "AC", "AP"]: continue

            
            # Parse the AP file
            parsedData = self.parseFile(strFileFormat, f"{strLIFEJUrl}/{fileName}", strEncoding)
            print(f"The parsed data is <{parsedData}>")
            _header = {}
            _tail = {}
            for _line in parsedData:
              strRowType = ""
              if _line['DataType'] == "1":
                strRowType = "1"
                vecNewFile.append(self.getLineStr(fileFormatConfig, _line))
                vecBankCodeFile.append(f"{strProcessDate},{_line['Account']},{strBankCode},")
                
                if strBankCode in configData['CUST_BANK_INFO']:
                  _line['CustCode'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['CustCode'], fileFormatConfig['Header']['CustCode'])
                  _line['CustName'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['CustName'], fileFormatConfig['Header']['CustName'])
                  _line['BankCode'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['BankCode'], fileFormatConfig['Header']['BankCode'])
                  _line['BankName'] = self.RightPadSpace(configData['CUST_BANK_INFO'][strBankCode]['BankName'], fileFormatConfig['Header']['BankName'])
                _header = _line

              if _line['DataType'] == "2":

                # If the transfer account code is same to destination
                if _header['BankCode'] == _line['BankCode'] and \
                  _header['BranchCode'] == _line['BranchCode'] and \
                  _header['Account'] == _line['Account']:
                  strRowType = "SAMEACC"
                  vecSameAccount.append(self.getLineStr(fileFormatConfig, _line))
                  mpSameAccount[fileName] = fileName

                  vecDeleteRow.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},SAME ACCOUNT,1,{_line['Amount']},{self.getLineStr(fileFormatConfig, _line)},")
                  vecTransLog.append({"process_date": strProcessDate, "bank_code": strBankCode, "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']), "record_type": "SAME ACCOUNT", "row_count": 1, "row_amount": _line['Amount'], "row_detail": self.getLineStr(fileFormatConfig, _line)})
                # If the accout is 0000000
                elif _header['Account'] == "0000000":
                  strRowType = "ALL0"
                  vecALL0Account.append(self.getLineStr(fileFormatConfig, _line))
                  mpAll0[fileName] = fileName

                  vecDeleteRow.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},0000000 ACCOUNT,1,{_line['Amount']},{self.getLineStr(fileFormatConfig, _line)},")
                  vecTransLog.append({"process_date": strProcessDate, "bank_code": strBankCode, "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']), "record_type": "0000000 ACCOUNT", "row_count": 1, "row_amount": _line['Amount'], "row_detail": self.getLineStr(fileFormatConfig, _line)})
                # General case
                else:
                  strRowType = "2"
                  vecNewFile.append(self.getLineStr(fileFormatConfig, _line))
                  lngSumAmount  = lngSumAmount + int(_line['Amount'])
                  lngSumCount += 1
                vecRtn.append(f",{strProcessDate},{strBankCode},{_header['ProcessDate']},{self.getLineStr(fileFormatConfig, _line)},{strRowType},")
                # Todo : replace start date 
                vecTransRow.append({"process_date": strProcessDate, "bank_code": _line['BankCode'], "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']), "row_detail": self.getLineStr(fileFormatConfig, _line), "row_type": strRowType})

              if _line['DataType'] == "8":
                _line['TotalAcount'] = self.LeftPadZero(lngSumCount, fileFormatConfig['Tail']['TotalAcount'])
                _line['TotalAmount'] = self.LeftPadZero(lngSumAmount, fileFormatConfig['Tail']['TotalAmount'])
                vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

              if _line['DataType'] == "9":
                vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

            self.txtFileWrite(vecNewFile, f"{strLIFEJUrl}/{fileName}.new", strEncoding)
        
            if len(vecSameAccount) > 0:
              _fileName = self.GetFileNameWithTS(configData['FILE_SAME_ACCOUNT_NAME_PATTERN'], strBankCode)
              self.txtFileWrite(vecSameAccount, f"{configData['LOG_FOLDER_BACKUP']}/{_fileName}", strEncoding)

            if len(vecALL0Account) > 0:
              _fileName = self.GetFileNameWithTS(configData['FILE_ALL0_ACCOUNT_NAME_PATTERN'], strBankCode)
              self.txtFileWrite(vecALL0Account, f"{configData['LOG_FOLDER_BACKUP']}/{_fileName}", strEncoding)
        
            vecFileAccounts.append(f"{strBankCode},{strProcessDate},{self.getFiveAccounts(parsedData)}")

        self.txtFileWrite(vecFileAccounts, f"{configData['FILE_FIVE_ACCOUNT']}", strEncoding)

        vecAll0Sort = self.sortFile(mpAll0)

        vecSameAccSort = self.sortFile(mpSameAccount)

        self.txtFileWrite(vecBankCodeFile, strFileMarkBankcode, strEncoding)

        self.txtFileWrite([str(len(vecBankCodeFile))], strFileMarkWaiting, strEncoding)

        self.insertTransRow(vecTransRow)

        self.insertTransLog(vecTransLog)

        return {
          "DBROW" : vecRtn,
          "MAIL_ALL0": vecAll0Sort,
          "MAIL_SAMEACC" : vecSameAccSort,
          "DELETED_ROW" : vecDeleteRow
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



        