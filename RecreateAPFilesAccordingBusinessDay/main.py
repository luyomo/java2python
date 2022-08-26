import logging
#import adal
import azure.functions as func
from azure.storage.fileshare import ShareServiceClient
from azure.storage.fileshare import ShareDirectoryClient
import pyodbc 
import os

from BTMU_PKG.common.common import Common
from BTMU_PKG.upload.fetchfromGL import fetchfromGL
from ..shared_code import Util

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Fetch the config file from remote
    configFile = req.params.get('ConfigFile')
    if not configFile:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            configFile = req_body.get('ConfigFile')

    bizDate = req.params.get('BizDate')
    if not bizDate:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            bizDate = req_body.get('BizDate')

    hisAPFiles = req.params.get('HisAPFiles')
    if not hisAPFiles:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            hisAPFiles = req_body.get('HisAPFiles')

    print(f"The config file name is {configFile}")
    print(f"The biz date name is {bizDate}")
    print(f"The ap files are {hisAPFiles}")
    __connection_string = os.getenv("AzureWebJobsStorage")
    #__share_name = os.getenv("AzureFASShareName")
    __local_dir = os.getenv("AzureFuncLocalDir")

    logging.info(f"The variable is {__connection_string}")
    #logging.info(f"The variable is {__share_name}")
    if __local_dir == None: __local_dir = "/tmp"
    logging.info(f"Local dir is {__local_dir}")

    insFetch = fetchfromGL(configFile, __connection_string, __local_dir)
    #insFetch = fetchfromGL("btmu-data/etc/config.json", __connection_string, __local_dir)
    insFetch.execute(bizDate, hisAPFiles)

    if hisAPFiles:
        return func.HttpResponse(f"Hello, {hisAPFiles}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
