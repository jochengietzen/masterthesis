import os
import sys
abspath = os.path.abspath

dir_root = abspath(os.path.join(os.path.curdir))
dir_data = os.path.join(dir_root, 'data')
dir_datafiles = os.path.join(dir_data, 'datafiles')
dir_sessions = os.path.join(dir_data, 'flask_session')

def createdirs():
    print('Creating dirs', file=sys.stdout)
    for dire in [dir_data, dir_datafiles, dir_sessions]:
        print(dire, file=sys.stdout)
        if not os.path.exists(dire):
            print('MK', file=sys.stdout)
            os.mkdir(dire)

percistency = dict(persistence=True, persistence_type='session')
plotlyConf = dict(
    config = dict(displaylogo = False),
    layout = dict(),
    styles = dict(
        fullsize = {'width': '95vw', 'height': '300px'},
        supersize = {'width': '95vw', 'height': '600px'},
        smallCorner = {'width': '30vw', 'height': '180px'}
    ),
    
)
colorpalette = dict(
        muted_blue = '#1f77b4',
        safety_orange = '#ff7f0e',
        cooked_asparagus_green = '#2ca02c',
        brick_red = '#d62728',
        muted_purple = '#9467bd',
        chestnut_brown = '#8c564b',
        raspberry_yogurt_pink = '#e377c2',
        middle_gray = '#7f7f7f',
        curry_yellow_green = '#bcbd22',
        blue_teal = '#17becf' 
    )

colormap = lambda ind: list(colorpalette.values())[ind % len(colorpalette)]
