import logging
import azure.functions as func
from azure.storage.fileshare import ShareServiceClient
from azure.storage.fileshare import ShareDirectoryClient
import pyodbc
import os, json, sys

from BTMU_PKG.upload.readRowLIFEJ import readRowLIFEJ

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    configFile = req.params.get('ConfigFile')
    if not configFile:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            configFile = req_body.get('ConfigFile')

    # The App Id and ClientSecret are used for testing. 
    # The prod app use MSI_SECRET as the DB crentials while the 
    # test environment use the 
    app_id = req.params.get('AppId')
    if not app_id:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse("AppId value is an error.", status_code=400)
        else:
            app_id = req_body.get('AppId')

    client_secret = req.params.get('ClientSecret')
    if not client_secret:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse("ClientSecret value is an error.", status_code=400)
        else:
            client_secret = req_body.get('ClientSecret')

    sqlserver_url = req.params.get('SQLServerUrl')
    if not sqlserver_url:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse("SQLServerUrl value is an error.", status_code=400)
        else:
            sqlserver_url = req_body.get('SQLServerUrl')

    dbname = req.params.get('DBName')
    if not dbname:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse("DBName value is an error.", status_code=400)
        else:
            dbname = req_body.get('DBName')

    schema = req.params.get('Schema')
    if not schema:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse("Schema value is an error.", status_code=400)
        else:
            schema = req_body.get('Schema')

    callerName = req.params.get('CallerName')
    if not schema:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse("Caller name is an error.", status_code=400)
        else:
            callerName = req_body.get('CallerName')


    __connection_string = os.getenv("AzureWebJobsStorage")

    # This is used for the testing. The test dir will be used variable because
    # in the windows, we have to define one while in the unix prod, the /tmp is used
    # to keep the temporary file.
    __local_dir = os.getenv("AzureFuncLocalDir")
    

    logging.info(f"The variable is {__connection_string}")
    #logging.info(f"The variable is {__share_name}")
    if __local_dir == None: __local_dir = "/tmp"
    logging.info(f"Local dir is {__local_dir}")

    insLogLIFEJ = readRowLIFEJ(configFile, __connection_string, __local_dir)
    insLogLIFEJ.setDBConfig(sqlserver_url, dbname, app_id, client_secret, "", callerName)
    
    retData = insLogLIFEJ.execute()
    retData["Status"] = "Success"

    return func.HttpResponse(
            json.dumps(retData),
            status_code=200,
            mimetype="application/json"
        )
    