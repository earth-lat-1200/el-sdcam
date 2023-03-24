import git
import logging
import datetime

g = git.cmd.Git("https://github.com/SFillip/el-sdcam.git")
currentDt = datetime.datetime.now()
logging.basicConfig(filename='updateLog.log', encoding='utf-8', level=logging.INFO)
try : 
    g.pull()
    logging.info('Complete (' + str(currentDt) + ')')
except Exception as e :
    logging.warning('Error (' + str(currentDt) + ')')