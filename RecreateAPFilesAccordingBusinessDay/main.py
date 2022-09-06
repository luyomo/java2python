import logging
import azure.functions as func
from azure.storage.fileshare import ShareServiceClient
from azure.storage.fileshare import ShareDirectoryClient
import os
import json
import pyodbc

from BTMU_PKG.common.common import Common
from BTMU_PKG.upload.fetchfromGL import fetchfromGL

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

    if hisAPFiles is None:
        hisAPFiles = []
    __connection_string = os.getenv("AzureWebJobsStorage")
    # __share_name = os.getenv("AzureFASShareName")
    __local_dir = os.getenv("AzureFuncLocalDir")

    logging.info(f"The variable is {__connection_string}")
    # logging.info(f"The variable is {__share_name}")
    if __local_dir is None:
        __local_dir = "/tmp"
    logging.info(f"Local dir is {__local_dir}")

    insFetch = fetchfromGL(configFile, __connection_string, __local_dir)
    if bizDate is None:
        return func.HttpResponse(
            json.dumps({"Status": "Failure", "ErrorMessage": "Please specify the BizDate like {'BizDate': '20220101'}"}),
            status_code=400,
            mimetype="application/json")
    retData = insFetch.execute(bizDate, hisAPFiles)

    retData["Status"] = "Success"

    return func.HttpResponse(
            json.dumps(retData),
            status_code=200,
            mimetype="application/json"
        )
