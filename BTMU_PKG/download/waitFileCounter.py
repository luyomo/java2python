from ..common.common import Common
import os
import logging
from datetime import datetime
from datetime import timedelta
import pyodbc


class waitFileCounter(Common):
    def __init__(self, configFile, storageConnectionStr, localDir, callerName):
        # super().__init__(configFile, storageConnectionStr, localDir)
        Common.__init__(self, configFile, storageConnectionStr, localDir)
        print(f"The config file is {self.configFile}")
        self.__callerName = callerName

    def execute(self):
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
        fileFormatConfig = self.readConfig(strFileFormat)

        # Get the current date as the process date
        strProcessDate = datetime.today().strftime('%Y%m%d')
        logging.debug(f"Current date(process date) : {strProcessDate}")

        vecDeleteRow = []
        vecBankCodeFile = []
        # Used to keep the data to output it file

        cntFromDB = self.fetchWaitfilesFromDB('20220815', 31)
        print(f"The count from DB is {cntFromDB}")
        
        if 1 == 1:
            return {"Status": "Success"}
        # files = self.listShareFile(strLIFEJUrl)
        # ---------- Loop all the files from the AP directory
        for file in files:
            vecNewFile = []         # Keep the data for new file(Remove the ALL0 and SameAccount and re-sum the data)
            vecSameAccount = []     # Keep the same account data to output to file
            vecALL0Account = []     # Keep the all0 data to putput to file

            fileName = file['name']  # File name

            # To remove since it has been got from the main branch
            # strProcessDate = datetime.today().strftime('%Y%m%d')
            # print(f"current date is {strProcessDate}")
            # vecBankCodeFile

            lngSumAmount = 0       # New sum account for new file(Remove All0 and Same account data)
            lngSumCount = 0       # Same to lngSumAmount

            strBankCode = fileName[0:2]      # Get the bank code: J1/J3/AC/Ap
            print(f"The bank code is {strBankCode}")

            # Skip if the bank code is not in the list
            if strBankCode not in ["J1", "J3", "AC", "AP"]:
                continue

            # Todo: Skip if the file is directory.

            # Parse the AP file
            parsedData = self.parseFile(strFileFormat, f"{strLIFEJUrl}/{fileName}", strEncoding)
            logging.debug(f"Parsed data: <{parsedData}>")

            _header = {}         # Keep the header to get the meta data and same account judgement
            # _tail = {}
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
                        _line['CustCode'] = self.RightPadSpace(
                            configData['CUST_BANK_INFO'][strBankCode]['CustCode'],
                            fileFormatConfig['Header']['CustCode'])
                        _line['CustName'] = self.RightPadSpace(
                            configData['CUST_BANK_INFO'][strBankCode]['CustName'],
                            fileFormatConfig['Header']['CustName'])
                        _line['BankCode'] = self.RightPadSpace(
                            configData['CUST_BANK_INFO'][strBankCode]['BankCode'],
                            fileFormatConfig['Header']['BankCode'])
                        _line['BankName'] = self.RightPadSpace(
                            configData['CUST_BANK_INFO'][strBankCode]['BankName'],
                            fileFormatConfig['Header']['BankName'])
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

                        vecDeleteRow.append(
                            f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},SAME ACCOUNT,1,\
                            {_line['Amount']},{self.getLineStr(fileFormatConfig, _line)},")
                        vecTransLog.append(
                            {"process_date": strProcessDate,
                             "bank_code": strBankCode,
                             "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']),
                             "record_type": "SAME ACCOUNT",
                             "row_count": 1,
                             "row_amount": _line['Amount'],
                             "row_detail": self.getLineStr(fileFormatConfig, _line)})
                    # If the accout is 0000000
                    elif _line['Account'] == "0000000":
                        # 1. Output the data into file
                        # 2. Output the data to trans_log to show the invalid data
                        # 3. Remove it from the new file.
                        strRowType = "ALL0"
                        vecALL0Account.append(self.getLineStr(fileFormatConfig, _line))
                        mpAll0[fileName] = fileName

                        vecDeleteRow.append(f",{strProcessDate},,{strBankCode},{_header['ProcessDate']},\
                            0000000 ACCOUNT,1,{_line['Amount']}, \
                            {self.getLineStr(fileFormatConfig, _line)},")
                        vecTransLog.append(
                            {"process_date": strProcessDate,
                             "bank_code": strBankCode,
                             "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']),
                             "record_type": "0000000 ACCOUNT",
                             "row_count": 1,
                             "row_amount": _line['Amount'],
                             "row_detail": self.getLineStr(fileFormatConfig, _line)})
                        # General case
                    else:
                        strRowType = "2"
                        vecNewFile.append(self.getLineStr(fileFormatConfig, _line))

                        # Calculate the new sum and count for the new file
                        lngSumAmount = lngSumAmount + int(_line['Amount'])
                        lngSumCount += 1

                    # Keep the data to output the data to file
                    vecRtn.append(f",{strProcessDate},{strBankCode},{_header['ProcessDate']},\
                      {self.getLineStr(fileFormatConfig, _line)},{strRowType},")
                    # Todo : replace start date
                    # Keep the data to insert it into dxc.trans_row 
                    vecTransRow.append(
                        {"process_date": strProcessDate,
                         "bank_code": _line['BankCode'],
                         "pay_date": self.findYYYYMMDD('20220801', 30, _header['ProcessDate']),
                         "row_detail": self.getLineStr(fileFormatConfig, _line),
                         "row_type": strRowType})

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

            retTimestamp = self.getLastModifiedTimestamp(f"{strLIFEJUrl}/{fileName}")
            # arrNewFiles.append({"FileName": f"{strLIFEJUrl}/{fileName}", "LastModifiedDate": retTimestamp})
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
          "Status": "Success",
          "Email": {
            "LastModification": arrNewFiles,
            "InvalidSummary": arrDeleted
          }
        }

        return vecRtn

    def fetchWaitfilesFromDB(self, startDate, theDays):
        def dbExecute(cursor):
            # retData = []
            try:
                __query = f"select count(*) as waiting_file from dxc.transbiz_his \
                  where target_date between '{startDate}' and DATEADD(day, {theDays}, '{startDate}') \
                    and (SIGN_STATUS is null OR SIGN_STATUS ='N') \
                    and email_processed = 'U'"

                logging.info(f"the query is {__query}")
                cursor.execute(__query)
                row = cursor.fetchone()
                print(f"The file format is {row}")
                return row[0]
                # return row['waiting_file']
            except pyodbc.Error as ex:
                sqlstate = ex.args[0]
                logging.info(f"Failed on the db: {sqlstate}")

        print(f"This is the testing scripts ... ... ")
        return self.executeDB(dbExecute)
