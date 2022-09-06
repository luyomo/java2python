import logging
import azure.functions as func
from azure.storage.fileshare import ShareServiceClient
from azure.storage.fileshare import ShareDirectoryClient
import pyodbc
import os
import json
import sys


from BTMU_PKG.upload.getZenkakuFileName import getZenkakuFileName


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a TransBizRowLogAccordingBusinessDay request.')

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"Status": "Failure", "ErrorMessage": "ConfigFile value is an error."}),
            status_code=400,
            mimetype="application/json")
    else:
        hankakuFiles = req_body.get('HankakuFiles')

    """
    # The App Id and ClientSecret are used for testing. 
    # The prod app use MSI_SECRET as the DB crentials while the 
    # test environment use the 
    app_id = req.params.get('AppId')
    if not app_id:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"Status": "Failure", "ErrorMessage": "AppId value is an error."}),
                status_code=400,
                mimetype="application/json")
        else:
            app_id = req_body.get('AppId')

    client_secret = req.params.get('ClientSecret')
    if not client_secret:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"Status": "Failure", "ErrorMessage": "ClientSecret value is an error."}),
                status_code=400,
                mimetype="application/json")
        else:
            client_secret = req_body.get('ClientSecret')

    sqlserver_url = req.params.get('SQLServerUrl')
    if not sqlserver_url:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"Status": "Failure", "ErrorMessage": "SQLServerUrl value is an error."}),
                status_code=400,
                mimetype="application/json")
        else:
            sqlserver_url = req_body.get('SQLServerUrl')

    dbname = req.params.get('DBName')
    if not dbname:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"Status": "Failure", "ErrorMessage": "DBName value is an error."}),
                status_code=400,
                mimetype="application/json")
        else:
            dbname = req_body.get('DBName')

    schema = req.params.get('Schema')
    if not schema:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"Status": "Failure", "ErrorMessage": "Schema value is an error."}),
                status_code=400,
                mimetype="application/json")
        else:
            schema = req_body.get('Schema')

    callerName = req.params.get('CallerName')
    if not schema:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"Status": "Failure", "ErrorMessage": "Caller name is an error."}),
                status_code=400,
                mimetype="application/json")
        else:
            callerName = req_body.get('CallerName')
    """

    """
    # Get the storage connection string
    __connection_string = os.getenv("AzureWebJobsStorage")
    logging.info(f"The variable is {__connection_string}")
    """

    """
    # This is used for the testing. The test dir will be used variable because
    # in the windows, we have to define one while in the unix prod, the /tmp is used
    # to keep the temporary file.
    __local_dir = os.getenv("AzureFuncLocalDir")
    if __local_dir is None:
        __local_dir = "/tmp"
    logging.info(f"Local dir is {__local_dir}")
    """

    #insReadLIFEJ = readRowLIFEJ(configFile, __connection_string, __local_dir, callerName)
    #insReadLIFEJ.setDBConfig(sqlserver_url, dbname, app_id, client_secret, "")

    #retData = insReadLIFEJ.execute()

    #if retData['Status'] == "Success":
    #    statusCode = 200

    text = "This is the test"
    print(f"source data is <{text}>")
    print(f"The changed data is <{text.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))}>")

    # print(mojimoji.han_to_zen("abcde12345‚ ‚è‚Ü‚·‚©", digit=True, ascii=True))

    insGetZenkakuFileName = getZenkakuFileName()
    retData = insGetZenkakuFileName.execute(hankakuFiles, "sjis")

    ret = {
        "Status": "Success",
        "ZenkakuFiles": retData
    }
    statusCode = 200
    print(f"The return value is {ret}")
    return func.HttpResponse(
        # json.dumps({"Status": "Success"}),
        json.dumps(ret),
        status_code=statusCode,
        mimetype="application/json"
    )
