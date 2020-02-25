from webapp.jgietzen.Data import Data
from webapp.helper import log
from webapp.config import dir_data, dir_rawdata, dir_datafiles
import dill as pkl
from os.path import join
import os
import re
import pandas as pd
import numpy as np

artificialData = join(dir_rawdata, 'artificialData')
ucrAndRealworldData = join(dir_rawdata, 'ucrAndRealworld')

def readArtificialFiles(path=artificialData):
    files = [os.path.abspath(os.path.join(path, fil)) for fil in os.listdir(path) if '.csv' in fil]
    for fil in files:
        log('Reading', fil)
        df = pd.read_csv(fil)
        data = Data(df, column_sort='idx',
            filename = re.sub('.csv', '', os.path.basename(fil)) + '_signalChange',
            originalfilename = re.sub('.csv', '_signalChange.csv', os.path.basename(fil)))
        log('Set columns for', fil)
        data.set_column_sort('time')
        data.set_has_timestamp_value(True)
        if 'yclean-signalChange' in df.columns.tolist():
            data.set_relevant_columns(['yclean-signalChange'])
            data.set_column_outlier(['outlierclean'])
            # yclean-noise': y, 'yclean-signalChange' : y2, 'outlierclean': out,
            #    'ynoisy-noise': yNoisy, 'ynoisy-signalChange' : y2Noisy, 'outliernoisy': outNois
        else:
            data.set_relevant_columns(['ynoisy-signalChange'])
            data.set_column_outlier(['outliernoisy'])
        data.save()
        log('Precalculate1', fil)
        data.precalculate()
        data.precalculatePlots()
        data.save()
        log('Done1')
        if np.any([file2.endswith(re.sub('.csv', '', os.path.basename(fil))) for file2 in os.listdir(dir_datafiles)]):
            continue
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
        log('Precalculate2', fil)
        data.precalculate()
        data.precalculatePlots()
        data.save()
        log('Done2')
    return data

def readUcrAndRealworld(path=ucrAndRealworldData):
    files = [os.path.abspath(os.path.join(path, fil)) for fil in os.listdir(path) if '.csv' in fil]
    for fil in files:
        log('Reading', fil)
        df = pd.read_csv(fil)
        if np.any([file2.endswith(re.sub('.csv', '', os.path.basename(fil))) for file2 in os.listdir(dir_datafiles)]):
            continue
        data = Data(df, column_sort='tsid',
            filename = re.sub('.csv', '', os.path.basename(fil)),
            originalfilename = os.path.basename(fil))
        log('Set columns for', fil)
        data.set_column_sort('time')
        data.set_has_timestamp_value(False)
        data.set_column_outlier([col for col in df.columns.tolist() if col in ['lof', 'isof', 'ee']])
        data.set_relevant_columns([col for col in df.columns.tolist() if col not in ['tsid', 'time', 'lof', 'isof', 'ee']])
        data.save()
        log('Precalculate', fil)
        data.precalculate()
        data.precalculatePlots()
        data.save()
        log('Done')

# readUcrAndRealworld()
readArtificialFiles()