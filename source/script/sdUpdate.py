import git
import logging
import datetime

gitUrl = git.cmd.Git("https://github.com/SFillip/el-sdcam.git")
logging.basicConfig(filename='updateLog.log', encoding='utf-8', level=logging.INFO)
try : 
    ##Wenn pull erfolgreich war wird Status und Zeit geloggt
    logging.info(gitUrl.pull() + ' ' + str(datetime.datetime.now()))
except Exception as e :
    ##Wenn pull nicht erfolgreich war wird entsprechende Fehlermeldung und Zeit geloggt
    logging.warning(str(e) + ' ' + str(datetime.datetime.now()))