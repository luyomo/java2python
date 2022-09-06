import logging
from azure.storage.fileshare import ShareFileClient
from azure.storage.fileshare import ShareDirectoryClient
import json
import time
import pyodbc
import os
import adal
import struct
from datetime import datetime
from datetime import timedelta
import numpy as np


class Common:
    def __init__(self, configFile, storageConnectionStr, localDir) -> None:
        self.connectionStr = storageConnectionStr
        self.configFile = configFile
        self.localDir = localDir
        self.configData = self.readConfig(configFile)
        if self.configData['SQLSERVER_URL'] is not None:
            self.__sqlserver_url = self.configData['SQLSERVER_URL']
        if self.configData['DBName'] is not None:
            self.__dbname = self.configData['DBName']

    def readShareFile(self, fileName):
        retFileName = self.parseFileName(fileName)
        print(f"Original file is {fileName}, share file: {retFileName['shareFile']}, file name: {retFileName['fileName']}")

        file_client = ShareFileClient.from_connection_string(conn_str=self.connectionStr, share_name=retFileName['shareFile'], file_path=retFileName['fileName'])
        localFileName = f"{self.localDir}/{int(time.time())}"
        with open(localFileName, "wb") as file_handle:
            data = file_client.download_file()
            data.readinto(file_handle)

        return localFileName

    def getLastModifiedTimestamp(self, fileName):
        retFileName = self.parseFileName(fileName)
        print(f"Original file is {fileName}, share file: {retFileName['shareFile']}, file name: {retFileName['fileName']}")

        file_client = ShareFileClient.from_connection_string(conn_str=self.connectionStr, share_name=retFileName['shareFile'], file_path=retFileName['fileName'])
        retAttr = file_client.get_file_properties()
        return retAttr['last_modified'].strftime('%Y/%m/%d %H:%M:%S')

    def listShareFile(self, folder):
        retFileName = self.parseFileName(folder)
        print(f"Original file is {folder}, share file: {retFileName['shareFile']}, file name: {retFileName['fileName']}")

        service = ShareDirectoryClient.from_connection_string(conn_str=self.connectionStr, share_name=retFileName['shareFile'], directory_path=retFileName['fileName'])
        fileList = list(service.list_directories_and_files())
        return fileList

    def copyShareFile(self, sourceFile, destinationFile):
        srcRetFileName = self.parseFileName(sourceFile)
        print(f"Original file is {sourceFile}, share file: {srcRetFileName['shareFile']}, file name: {srcRetFileName['fileName']}")
        destRetFileName = self.parseFileName(destinationFile)
        print(f"Original file is {destinationFile}, share file: {destRetFileName['shareFile']}, file name: {destRetFileName['fileName']}")

        file_client = ShareFileClient.from_connection_string(conn_str=self.connectionStr, share_name=srcRetFileName['shareFile'], file_path=srcRetFileName['fileName'])
        localFileName = f"{self.localDir}/{int(time.time())}"
        print(f"The file name is {localFileName}")
        with open(localFileName, "wb") as file_handle:
            data = file_client.download_file()
            data.readinto(file_handle)

        file_dest_client = ShareFileClient.from_connection_string(
            conn_str=self.connectionStr,
            share_name=destRetFileName['shareFile'],
            file_path=destRetFileName['fileName'])
        with open(localFileName, "rb") as source_file:
            file_dest_client.upload_file(source_file)

    def getLineStr(self, configData, line):
        retStr = ""
        _configData = {}
        if line['DataType'] == "1":
            _configData = configData['Header']
        if line['DataType'] == "2":
            _configData = configData['Body']
        if line['DataType'] == "8":
            _configData = configData['Tail']
        if line['DataType'] == "9":
            _configData = configData['End']

        for key in _configData:
            retStr += line[key]

        return retStr

    def uploadData(self, configFile, data, dataFile, encoding):

        print(f"Uploading data configFile: {configFile}, data: {data}, dataFile:{dataFile}, encoding: {encoding}")
        retFileName = self.parseFileName(dataFile)
        print(f"Original file is {dataFile}, share file: {retFileName['shareFile']}, file name: {retFileName['fileName']}")

        configData = self.readConfig(configFile)
        localFileName = f"{self.localDir}/{int(time.time())}"

        newFile = open(localFileName, "w")
        for _row in data:
            _configData = {}
            if _row['DataType'] == "1":
                _configData = configData['Header']
            if _row['DataType'] == "2":
                _configData = configData['Body']
            if _row['DataType'] == "8":
                _configData = configData['Tail']
            if _row['DataType'] == "9":
                _configData = configData['End']

            for key in _configData:
                newFile.write(_row[key])
            newFile.write("\n")
        # newFile.write("9\n")
        newFile.close()

        file_dest_client = ShareFileClient.from_connection_string(conn_str=self.connectionStr, share_name=retFileName['shareFile'], file_path=retFileName['fileName'])
        with open(localFileName, "rb") as source_file:
            file_dest_client.upload_file(source_file)

    def txtFileWrite(self, data, dataFile, encoding):
        print(f"txtFileWrite : data: {data}, dataFile:{dataFile}, encoding: {encoding}")
        retFileName = self.parseFileName(dataFile)
        print(f"Original file is {dataFile}, share file: {retFileName['shareFile']}, file name: {retFileName['fileName']}")

        localFileName = f"{self.localDir}/{int(time.time())}"

        newFile = open(localFileName, "w")
        for _row in data:
            newFile.write(_row)
            newFile.write("\n")
        newFile.close()

        file_dest_client = ShareFileClient.from_connection_string(conn_str=self.connectionStr, share_name=retFileName['shareFile'], file_path=retFileName['fileName'])
        with open(localFileName, "rb") as source_file:
            file_dest_client.upload_file(source_file)

    def parseFileName(self, fileName):
        arrValue = fileName.split("/")
        return {"shareFile": arrValue[0], "fileName": "/".join(arrValue[1:])}

    def readConfig(self, configFile):
        print(f" --------------- The file to be parsed <{configFile}>")

        downloadFile = self.readShareFile(configFile)

        with open(downloadFile,  encoding="utf-8") as file:
            metaData = json.load(file)

        return metaData

    def parseFile(self, configFile, dataFile, encoding):
        arrayData = []
        configData = self.readConfig(configFile)
        # self.__logger.debug(f"Header config : {configData['Header']}")
        # self.__logger.debug(f"Body config   : {configData['Body']}")
        # self.__logger.debug(f"Tail config   : {configData['Tail']}")
        downloadFile = self.readShareFile(dataFile)
        f = open(downloadFile, "r", encoding=encoding)
        try:
            for line in f:
                # self.__logger.debug(f"Line: {line}")
                dataType = line[0:1]
                # self.__logger.debug(f"Data Type: {dataType}")
                if dataType == "1":
                    retData = self.parseLine(line, configData['Header'], encoding)
                elif dataType == "2":
                    retData = self.parseLine(line, configData['Body'], encoding)
                elif dataType == "8":
                    retData = self.parseLine(line, configData['Tail'], encoding)
                elif dataType == "9":
                    retData = self.parseLine(line, configData['End'], encoding)

                arrayData.append(retData)
        finally:
            f.close()
        return arrayData

    def parseLine(self, inStr, config, encoding):
        bytesStr = inStr.replace("\n", "").encode(encoding)
        retMap = {}
        for key in config:
            # print(f"The config is <{key}> and {config[key]} ")
            # Todo: Return error if the format is not [number-number]
            pos = config[key].split("-")
            # print(f"The start is {pos[0]} and end is {pos[1]}")
            # Todo: Return error if it's not the number
            tmpBytes = bytesStr[int(pos[0])-1:int(pos[1])]
            retMap[key] = tmpBytes.decode(encoding)
            # retMap[key] = inStr[int(pos[0])-1:int(pos[1])]
        # print(f"This is the input mesage <{inStr}> ")
        # print(f"The map value is <{retMap}>")
        return retMap

    def HenkanZenkaku(self, inStr, encoding):
        _toReplace = ""
        for _char in inStr:
            # print(f"The character is {_char}")
            if len(_char.encode(encoding)) > 1:
                _toReplace = _toReplace + "\\" * len(_char.encode(encoding))
            else:
                _toReplace = _toReplace + _char
        # print(f"The body is ->|{_toReplace}|<-")
        return _toReplace

    def RightPadSpace(self, inStr, colLen):
        """Convert the format 10-20 -> 11
        Examle:
          input:
            inStr: 0005
            colLen:5-15
          output:
            0005______ (_ -> space)
        """
        pos = colLen.split("-")
        return inStr.ljust(int(pos[1]) - int(pos[0]) + 1)

    def LeftPadZero(self, inValue, colLen):
        """Convert the format 10-20 -> 11
        Examle:
          input:
            inStr: 1000
            colLen:5-15
          output:
            000000000001000
        """
        pos = colLen.split("-")
        return str(inValue).zfill(int(pos[1]) - int(pos[0]) + 1)

    def GetFileNameWithTS(self, _pattern, strBK):
        """ Generate the file name from pattern with date and bank code replacement

        Args:
            _pattern (_type_): DELETE_SAME_ACCOUNT_'yyyyMMdd'_BK.txt
            strBK (_type_): J1
        Return:
            DELETE_SAME_ACCOUNT_20220801_J1.txt
        """
        strDate = datetime.today().strftime('%Y%m%d')
        return _pattern.replace("'yyyyMMdd'", strDate).replace("BK", strBK)

    def provide_token(self, token_url, app_id, client_secret):
        context = adal.AuthenticationContext(self.__authority_url)
        token = context.acquire_token_with_client_credentials(
            token_url,
            app_id,
            client_secret)

        return token

    def setDBConfig(self, sqlserverUrl, dbName, appId, clientSecret, authorityUrl):
        if sqlserverUrl is not None:
            self.__sqlserver_url = sqlserverUrl
        if dbName is not None:
            self.__dbname = dbName
        self.__app_id = appId
        self.__client_secret = clientSecret
        self.__authority_url = authorityUrl

    def findYYYYMMDD(self, strPayDateFrom, strDays, strMMDD):
        """
        Example:
          (20220801, 31, 0804) -> 20220804 
          (20220801, 31, 0831) -> 20220831
          (20220801, 31, 0901) -> ''
        """
        payDateFrom = datetime.strptime(strPayDateFrom, '%Y%m%d')
        for idx in np.arange(1, int(strDays)):
            theDate = payDateFrom + timedelta(days=int(idx))
            if theDate.strftime('%m%d') == strMMDD:
                return theDate.strftime('%Y%m%d')
        return ""

    def executeDB(self, funcDBProc):
        ret = {}
        driver = "{ODBC Driver 17 for SQL Server}"
        connection_string = f"DRIVER={driver};SERVER={self.__sqlserver_url};DATABASE={self.__dbname}"
        try:
            if os.getenv("MSI_SECRET"):
                # If MSI is enabled, use MSI as the authentication.
                conn = pyodbc.connect(connection_string+';Authentication=ActiveDirectoryMsi')
                logging.info(f'Connection: MSI_SECRET')
            elif "DBUser" in self.configData:
                logging.info(f"The connection string is {connection_string}")
                logging.info(f"User: {self.configData['DBUser']}, password: {self.configData['DBPassword']}")
                conn = pyodbc.connect('DRIVER={SQL Server}'
                                      + f";SERVER={self.__sqlserver_url};DATABASE={self.__dbname};UID={self.configData['DBUser']};PWD={self.configData['DBPassword']}")
                logging.info(f"User/Password login")
            else:
                # otherwise use odal as the authentication
                db_token = self.provide_token('https://database.windows.net', self.__app_id, self.__client_secret)

                SQL_COPT_SS_ACCESS_TOKEN = 1256

                exptoken = b''
                for i in bytes(db_token['accessToken'], "UTF-8"):
                    exptoken += bytes({i})
                    exptoken += bytes(1)

                tokenstruct = struct.pack("=i", len(exptoken)) + exptoken
                conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: tokenstruct})
                logging.info(f'Connection: Token')
            cursor = conn.cursor()
            ret = funcDBProc(cursor)
            logging.info(f"The result is {ret}")
        # cursor.execute(f'TRUNCATE TABLE {schema}.Employee_AAD')
        # for index, row in src_df.iterrows():
        #    cursor.execute(f"Exec {schema}.usp_Employee_Insert_Update ?,?,?,?,?,?", row.EmployeeId, row.JPUserId,
        #                   row.InsimUserId, row.Department, row.BusinessPhone, row.Mail)
            conn.commit()
            cursor.close()
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            logging.info(f"Failed on the db: {ex}")
        return ret

    def FetchDBConn(self):
        # db_token = self.provide_token('https://database.windows.net', self.__app_id, self.__client_secret)
        try:
            driver = "{ODBC Driver 17 for SQL Server}"
            # sqlserver_url = "sqlsr-fas-dev-001.database.windows.net"
            sqlserver_url = "jaytestdbserver.database.windows.net"
            # dbname = "sqldb-fas-dev"
            dbname = "jaytestdb"
            connection_string = 'DRIVER='+driver+';SERVER='+sqlserver_url+';DATABASE='+dbname
            if os.getenv("MSI_SECRET"):
                logging.info(f'Connection: MSI_SECRET')
                logging.info(f"The MSI_SECRET is {os.getenv('MSI_SECRET')}")

                conn = pyodbc.connect(connection_string+';Authentication=ActiveDirectoryMsi')

            else:
                logging.info(f"No MSI_SECRET")
                return
            # SQL_COPT_SS_ACCESS_TOKEN = 1256

            # exptoken = b''
            # for i in bytes(db_token['accessToken'], "UTF-8"):
            #    exptoken += bytes({i})
            #    exptoken += bytes(1)

            # tokenstruct = struct.pack("=i", len(exptoken)) + exptoken
            # conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: tokenstruct})
            # logging.info(f'Connection: Token')
            cursor = conn.cursor()
            # cursor.execute(f'TRUNCATE TABLE {schema}.Employee_AAD')
            # for index, row in src_df.iterrows():
            #    cursor.execute(f"Exec select max(run_num) from dxc.transbiz_his")
            conn.commit()
            cursor.close()
        except pyodbc.Error as ex:
            # sqlstate = ex.args[0]
            logging.info(f"The error is {ex}")
