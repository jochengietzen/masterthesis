from webapp.jgietzen.Data import Data
from webapp.helper import log
from webapp.config import dir_data, dir_rawdata
import dill as pkl
from os.path import join
import os
import re
import pandas as pd

stdpath = join(dir_rawdata, 'artificialData')

def readFiles(path=stdpath):
    files = [os.path.abspath(os.path.join(path, fil)) for fil in os.listdir(path) if '.csv' in fil]
    for fil in files:
        log('Reading', fil)
        df = pd.read_csv(fil)
        data = Data(df, column_sort='idx',
            filename = re.sub('.csv', '', os.path.basename(fil)),
            originalfilename = os.path.basename(fil))
        log('Set columns for', fil)
        data.set_column_sort('time')
        data.set_has_timestamp_value(True)
        if 'yclean-noise' in df.columns.tolist():
            data.set_relevant_columns(['yclean-noise'])
            data.set_column_outlier(['outlierclean'])
            # yclean-noise': y, 'yclean-signalChange' : y2, 'outlierclean': out,
            #    'ynoisy-noise': yNoisy, 'ynoisy-signalChange' : y2Noisy, 'outliernoisy': outNois
        else:
            data.set_relevant_columns(['ynoisy-noise'])
            data.set_column_outlier(['outliernoisy'])
        data.save()
        log('Precalculate', fil)
        data.precalculate()
        data.precalculatePlots()
        data.save()
        log('Done')
    return data