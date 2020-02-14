import inspect
import tsfresh
import numpy as np
import re
insp = lambda fun: inspect.getsource(getattr(tsfresh.feature_extraction.feature_calculators, fun))
inspParse = lambda parse, fun: re.compile(parse).findall(insp(fun))
def inspType(fun): 
    normal = [inspParse(':return type: (.*)', fun), inspParse(':rtype: (.*)', fun)]
    #print(normal)
    if all(np.array(list(map(len, normal))) == 0):
        raise Exception('Didnt find a return type in\n{}'.format(insp(fun)))
    return normal[0 if len(normal[0]) > 0 else 1][0]

class Feature:
    
    __explanations = {
    'abs_energy': {'phrase': 'the sum of {variable}\'s squared values'},
    'has_duplicate_max': {'phrase': '{variable} [boolvalue] duplicate appearances of the maximum value',
                         'boolvaluechoice': 'has'},
    'has_duplicate_min': {'phrase': '{variable} [boolvalue] duplicate appearances of the minimum value'},
    'has_duplicate': {'phrase': '{variable} [boolvalue] duplicate appearances of any value'},
    'variance_larger_than_standard_deviation': {'phrase': 'the variance of {variable} [boolvalue] larger than it\'s standard deviation'},
    'sum_values': {'phrase': 'the sum of {variable}\'s values'},
    'mean_abs_change': {'phrase': 'the mean of the absolute changes of consecutive values of {variable}'},
    'mean_change': {'phrase': 'the mean of the changes of the consecutive values of {variable}'},
    'median': {'phrase': 'the median of {variable}'},
    'mean': {'phrase': 'the mean of {variable}'},
    'length': {'phrase': 'the length of {variable}'},
    'standard_deviation': {'phrase': 'the standard deviation of {variable}'},
    'variance': {'phrase': 'the variance of {variable}'},
    'skewness': {'phrase': 'the skewness of {variable}\'s distribution'},
    'kurtosis': {'phrase': 'the kurtosis of {variable}\'s distribution'},
    'absolute_sum_of_changes': {'phrase': 'the absolute sum of changes of {variable}'},
    'longest_strike_below_mean': {'phrase': 'the longest consecutive subsequence in {variable} that is smaller than it\'s mean'},
    'longest_strike_above_mean': {'phrase': 'the longest consecutive subsequence in {variable} that is bigger than it\'s mean'},
    'count_above_mean': {'phrase': 'the amount of values in {variable} that is above it\'s mean'},
    'count_below_mean': {'phrase': 'the amount of values in {variable} that is below it\'s mean'},
    'last_location_of_maximum': {'phrase': 'the last relative location {variable}\'s maximum'},
    'first_location_of_maximum': {'phrase': 'the first relative location {variable}\'s maximum'},
    'last_location_of_minimum': {'phrase': 'the last relative location {variable}\'s minimum'},
    'first_location_of_minimum': {'phrase': 'the first relative location {variable}\'s minimum'},
    'percentage_of_reoccurring_datapoints_to_all_datapoints': {'phrase': 'the percentage of reoccurring datapoints in {variable}'},
    'percentage_of_reoccurring_values_to_all_values': {'phrase': 'the percentage of reoccurring values in {variable}'},
    'sum_of_reoccurring_values': {'phrase': 'the sum of reoccurring values in {variable}'},
    'sum_of_reoccurring_data_points': {'phrase': 'the sum of reoccurring data points in {variable}'},
    'ratio_value_number_to_time_series_length': {'phrase': 'the percentage of unique values in {variable}'},
    'sample_entropy': {'phrase': 'the entropy of a smaple of {variable}'},
    'maximum': {'phrase': 'the maximum of {variable}'},
    'minimum': {'phrase': 'the minimum of {variable}'},
    'linear_trend': {'phrase': 'the linear least-squares regression of {variable}'},
    'agg_linear_trend': {'phrase': 'the linear least-squares regression of an aggregation of {variable}'},
    'number_crossing_m': {'phrase': 'the amount of crossings over m in {variable}'},
    'ratio_beyond_r_sigma': {'phrase': 'the ratio of values that are more than r*std away from the mean of {variable}'},
#   ------------- Difficult features ------–    
    'c3': {'phrase': 'the c3 value of {variable}'},
    'cid_ce': {'phrase': 'the complexity (after cid_ce) of the timeseries of {variable}'},
    'symmetry_looking': {'phrase': 'the distribution of {variable} [boolvalue] symmetric looking'},
    'quantile': {'phrase': 'the quantile of {variable}'},
    'autocorrelation': {'phrase': 'the autocorrelation of {variable}'},
    'agg_autocorrelation': {'phrase': 'the aggregated autocorrelation of {variable}'},
    'partial_autocorrelation': {'phrase': 'the partial autocorrelation of {variable}'},
    'large_standard_deviation': {'phrase': 'the standard deviation of {variable} [boolvalue] larger than r times (max - min)'},
    'number_cwt_peaks': {'phrase': 'the number of peaks in {variable} counted after ricker wavelet smoothing'},
    'number_peaks': {'phrase': 'the number of peaks in {variable}'},
    'binned_entropy': {'phrase': 'the entropy of the binned values of {variable}'},
    'range_count': {'phrase': 'the count of range of {variable}'},
    'value_count': {'phrase': 'the amount of occurences of in {variable}'},
    'ar_coefficient': {'phrase': 'the unconditional maximum likelihood of an autoregressive AR of {variable}'},
    'cwt_coefficients': {'phrase': 'Continuous wavelet transform for the Ricker wavelet of {variable}'},
    'change_quantiles': {'phrase': 'the {f_agg} {isabs}change of {variable} in a corridor on the y-Axis between the {ql} and {qh} quantiles',
                        'isabs': {'choices': ['', 'of the absolute ']}},
    'fft_coefficient': {'phrase': 'the one-dimensional discrete Fourier Transform coefficient for {variable}'},
    'fft_aggregated': {'phrase': 'the aggregated fft transformation of {variable}'},
    'approximate_entropy': {'phrase': 'the approximate entropy of {variable}'},
    'friedrich_coefficients': {'phrase': 'the Langevin model fitted deterministic dynamics of {variable} (friedrich coefficient)'},
    'max_langevin_fixed_point': {'phrase': 'the largest fixpoint of the Langevin model fitted deterministic dynamics of {variable}'},
    }
    
    def __init__(self, name, fromColumn, typ, params = None):
        self.name = name
        self.fromColumn = fromColumn
        self.typ = typ
        self.params = params
    
    @property
    def featureCharacteristics(self):
        return self.__explanations[self.name]

    @property
    def phrase(self):
        exp = self.featureCharacteristics
        ret = exp['phrase']
        params = self.params
        if params == None:
            ret = ret.format(variable=self.fromColumn)
        else:
            for param in [param for param in params if param in exp]:
                if 'choices' in exp[param]:
                    params[param] = exp[param]['choices'][int(params[param] == 'True')]
            ret = ret.format(variable=self.fromColumn, **params)
        ret = re.sub(r'\[', '{', ret)
        ret = re.sub(r'\]', '}', ret)
        return ret
    
    def valuePhrase(self, operator, value):
        phrase = self.phrase
        if self.typ == 'bool':
            if not self.sanity(operator[0], value):
                Exception('Not a sane literal')
            choices = ['has no/is not', 'has/is']
            chars = self.featureCharacteristics
            if 'boolvaluechoice' in chars:
                choices = [ch[0 if chars['boolvaluechoice'] == 'has' else 1] for ch in [c.split('/') for c in choices]]
            choice = choices[int(operator[0](1, value))]
            phrase = phrase.format(boolvalue=choice)
        elif self.typ in ['float', 'int']:
            comparison = operator[1]
            phrase = f'{phrase} is {comparison} {"{:.3f}".format(value)}'
        else:
            raise Exception('Not handled yet ' + self.typ)
        return phrase
    
    def __str__(self):
        return str(self.__dict__) + f'\n{self.featureCharacteristics}' + f'\n{self.phrase}\n'
    
    @staticmethod
    def sanity(operator, value):
        return operator(1, value) != operator(0,value)

    @staticmethod
    def exists(featurename):
        return featurename in Feature.__explanations
    
    @staticmethod
    def tryParse(columnname):
        try:
            return Feature.parseFeature(columnname)
        except:
            return False
    
    @staticmethod
    def parseFeature(columnname):
        prts = columnname.split('__')
        if len(prts) == 2 and not Feature.exists(prts[1]):
            Exception('FeatureNotParsable')
        elif len(prts) < 2:
            Exception('FeatureNotParsable')
        column = prts[0]
        featurename = prts[1]
        params = None
        if len(prts) > 2:
            params = {}
            for prt in prts[2:]:
                sp = prt.split('_')
                params['_'.join(sp[:-1])] = sp[-1]
        typ = inspType(featurename)
        return Feature(name = featurename, fromColumn = column, typ = typ, params = params)


from contrastive_explanation import Literal, Operator
import operator

class Explanation:
    
    def __init__(self, literal, features, fact = None, foil = None, weight = None, complete = False):
        assert type(literal) == Literal or (all([type(lit) == Literal for lit in literal]) and type(literal) == list), 'Only Literals are allowed. Either one Literal or a list'
        literal = literal if type(literal) == list else [literal]
        assert type(features) == list and all([type(feat) == str for feat in features]), 'Please provide a list of features'
        self.literal = literal
        self.__features = features
        self.fact = fact
        self.foil = foil
        self.weight = weight
        self.completeInput = complete
    
    def explainLiteral(self, literal):
        feature = self.features[literal.feature]
        if type(feature) == str:
            return f'{feature} is {literal.operator[1]} {literal.value}'
        return feature.valuePhrase(operator = literal.operator, value = literal.value)
        
    @property
    def operatorcorrected(self):
        operatorLookup = {
            'GEQ': (operator.ge, 'at least'),
            'SEQ': (operator.le, 'at most'),
            'EQ': (operator.eq, 'equal to'),
            'GT': (operator.gt, 'greater than'),
            'ST': (operator.lt, 'lesser than'),
            'NOTEQ': (operator.ne, 'not equal to')
        }
        return [
            Literal(
                feature=lit.feature,
                operator = operatorLookup[lit.operator.name],
                value = lit.value,
                categorical= lit.categorical
                )
            for lit in self.literal
        ]
    
    @property
    def features(self):
        return [Feature.parseFeature(feature) if Feature.tryParse(feature) != False else feature for feature in self.__features]
    
    def explain(self, html=False):
        literals = [self.operatorcorrected[s] for s in np.argsort([l.feature for l in self.literal])]
        literals = [self.explainLiteral(literal) for literal in literals]
        literals = " and ".join(literals) if not html else "<br />and ".join(literals)
        msg = ''
        if self.completeInput:
            msg = f'Predicted "{self.fact}" instead of "{self.foil}", because{"<br />" if html else ": "}{literals}'
            msg.format()
        else:
            msg = f'Decission was taken, because{"<br />" if html else ": "}{literals}'
        return msg
    
    def __str__(self):
        return f'literals: {self.literal}\nfeatures: {self.__features}'
    
    @staticmethod
    def fromContrastiveResult(explanationTuple, features, classes = None):
        assert len(explanationTuple) == 7, 'Unknown explanation format received'
        fact, foil, literals, _, _, _, weight = explanationTuple
        if type(classes) != type(None):
            fact, foil = classes[fact], classes[foil]
        return Explanation(literals, features, fact, foil, weight, complete = True)
        
