import os
import sys
abspath = os.path.abspath

dir_root = abspath(os.path.join(os.path.curdir, '..'))
dir_data = os.path.join(dir_root, 'data')
dir_datafiles = os.path.join(dir_data, 'datafiles')
dir_sessions = os.path.join(dir_data, 'flask_session')

for dire in [dir_data, dir_datafiles, dir_sessions]:
    if not os.path.exists(dire):
        os.mkdir(dire)
