import logging
#import adal
import azure.functions as func
from azure.storage.fileshare import ShareServiceClient
from azure.storage.fileshare import ShareDirectoryClient
import pyodbc
import os

from BTMU_PKG.upload.readRowLIFEJ import readRowLIFEJ

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    insLogLIFEJ = readRowLIFEJ("test", "test", "test")
    insLogLIFEJ.FetchDBConn()

    #configFile = req.params.get('ConfigFile')
    #if not configFile:
    #    try:
    #        req_body = req.get_json()
    #    except ValueError:
    #        pass
    #    else:
    #        configFile = req_body.get('ConfigFile')

    #__connection_string = os.getenv("AzureWebJobsStorage")
    ##__share_name = os.getenv("AzureFASShareName")
    #__local_dir = os.getenv("AzureFuncLocalDir")



    #logging.info(f"The variable is {__connection_string}")
    ##logging.info(f"The variable is {__share_name}")
    #if __local_dir == None: __local_dir = "/tmp"
    #logging.info(f"Local dir is {__local_dir}")

    #insLogLIFEJ = readRowLIFEJ(configFile, __connection_string, __local_dir)
    #insLogLIFEJ.FetchDBConn()
    #insLogLIFEJ = readRowLIFEJ("fas-etl")

    #insLogLIFEJ.execute()

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
