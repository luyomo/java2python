from ..common.common import Common
import os
import logging
from datetime import datetime
from datetime import timedelta
import mojimoji
import re


class getZenkakuFileName(Common):
    def __init__(self):
        pass
        
    def execute(self, hankakuFiles, encoding):
        retValue = []
        for file in hankakuFiles:
            if file["FileType"] == "AP":
                print(f"This is the AP code {file}")
                ret = re.match(r'^AP_PAY_BTMU_(\d+).txt$', file['File'])
                strBankCode = mojimoji.han_to_zen(f"AP{ret.group(1)}", digit=True, ascii=True)
                print(f"The result is {strBankCode}")
                retDate = re.match(r'^(\d\d)(\d\d)$', file['PayDate'])
                print(f"The month is {retDate.group(1)} and date is {retDate.group(2)}")
                zenMonth = mojimoji.han_to_zen(f"{retDate.group(1)}", digit=True, ascii=True)
                zenDay = mojimoji.han_to_zen(f"{retDate.group(2)}", digit=True, ascii=True)
                #zenFile = f"{zenMonth}{zenDay}{strBankCode}.txt"
                zenFile = f"{zenMonth}月{zenDay}日支払{strBankCode}.txt"
                print(f"The date is {zenFile}")
                file['ZenFile'] = zenFile
                file['BankCode'] = f"AP{ret.group(1)}"

                print(f"The file is {file}")
                retValue.append({"File": file["File"], "BankCode": f"AP{ret.group(1)}", "ZenFile": zenFile})

            else:
                retDate = re.match(r'^(\d\d)(\d\d)$', file['PayDate'])
                print(f"The month is {retDate.group(1)} and date is {retDate.group(2)}")
                zenMonth = mojimoji.han_to_zen(f"{retDate.group(1)}", digit=True, ascii=True)
                zenDay = mojimoji.han_to_zen(f"{retDate.group(2)}", digit=True, ascii=True)

                strBankCode = mojimoji.han_to_zen(file['FileType'], digit=True, ascii=True)
                zenFile = f"{zenMonth}月{zenDay}日支払{strBankCode}.txt"

                retValue.append({"File": file["File"], "BankCode": file["FileType"], "ZenFile": zenFile})

                print(f"The is the non ap bank code")

        return retValue