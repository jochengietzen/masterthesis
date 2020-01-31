
percistency = dict(persistence=True, persistence_type='session')
plotly = dict(
    config = dict(displaylogo = False),
    layout = dict()
)

def log(*args):
    import sys
    print(*args, file=sys.stdout)

def valueOrAlternative(kwargs, key, alternative=None):
    return kwargs[key] if key in kwargs else alternative

def keyValuesFilter(dic, keys):
    return {key: dic[key] for key in keys if key in list(dic.keys())}