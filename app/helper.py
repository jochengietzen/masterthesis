
percistency = dict(persistence=True, persistence_type='session')
plotlyConf = dict(
    config = dict(displaylogo = False),
    layout = dict(),
    style = {'width': '95vw', 'height': '300px'},
    
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

def log(*args):
    import sys
    print(*args, file=sys.stdout)

def valueOrAlternative(kwargs, key, alternative=None):
    return kwargs[key] if key in kwargs else alternative

def keyValuesFilter(dic, keys):
    return {key: dic[key] for key in keys if key in list(dic.keys())}