import pandas as pd
import numpy as np
import lime
import lime.lime_tabular
import sklearn
import sklearn.ensemble
import shap
import contrastive_explanation as ce

from webapp.helper import consecutiveDiff, log, specificKwargs
from webapp.jgietzen.Cachable import Cachable, cache

class OutlierExplanation(Cachable):
    
    def __init__(self, outlier, parent):
        super().__init__(internalStore=parent.internalStore, alwaysCheck= ['outlier', 'parent'], verbose=True)
        assert all([type(o) in [bool, np.bool_] for o in outlier]), 'Please provide your outlier data as boolean list/array, where True indicates an outlier'
        self.surrogates = {}
        self.lime = {}
        self.shap = {}
        self.cfoil = {}
        self.consecBlocks = None
        self.minimumOutliers = 2
        self.outlier = outlier
        self.parent = parent
        self.calcStandards()
        
    def npmap(self, mapping):
        return np.vectorize(lambda a: mapping[a] if a in mapping else a)

    def calcStandards(self):
        self.calcBlocks()
        # self.makeFeatureFrames()
        
    def calcBlocks(self):
        self.consecBlocks = consecutiveDiff(self.outlier)
        return self.consecBlocks

    @property
    def consecBlocksSortedForPlotting(self):
        blocks = self.consecBlocksForPlotting
        return [b for b in blocks if b[1][0] == 'outlier'] + [b for b in blocks if b[1][0] == 'inlier']

    @property
    def consecBlocksForPlotting(self):
        return [
            (b[0],
            ('outlier' if b[1][0] == True else 'inlier' ,b[1][1]),
            'indianred' if b[1][0] == True else 'limegreen'
            ) for b in self.consecBlocks
        ]
    
    @property
    def outlierBlocks(self):
        blocks = self.consecBlocks
        blocks = [block for block in blocks if block[1][0] and block[1][1] >= self.minimumOutliers]
        return blocks
    
    @property
    def consecBlocksLengths(self):
        return [bChar[1] for _, bChar in self.consecBlocks]


    @property
    def outlierBlocksLengths(self):
        return [bChar[1] for _, bChar in self.outlierBlocks]

    def makeFeatureFrames(self):
        lens = [bchar[1] for bl, bchar in self.outlierBlocks]
        for l in np.unique(lens):
            self.parent.calc_feature_frame(l)
    
    @property
    def getOutlierPartitions(self):
        counts = list(np.unique(self.outlier, return_counts=True))
        counts.append(self.npmap({True: 'outlier', False: 'inlier'})(counts[0]))
        counts.append(counts[1] / sum(counts[1]))
        counts.append(self.npmap({True: 'rgb(250,0,0)', False: 'rgb(0,250,0)'})(counts[0]))
        return counts
    
    def getOutlierAdjusted(self, adjustedToOutlierBlock = False):
        if adjustedToOutlierBlock == True:
            # TODO
            raise NotImplementedError
        else:
            return self.outlier

    def getDataframe(self, windowsize, adjustedToOutlierBlock = False, loseIndexCols = True):
        preddf = self.parent.get_feature_frame(windowsize=windowsize, adjustedToOutlierBlock = adjustedToOutlierBlock)
        if loseIndexCols == True:
            return preddf.drop(columns=[self.parent.column_sort, self.parent.column_id])
        return preddf
    
    def fitSurrogate(self, adjustedToOutlierBlock = False, **kwargs):
        # Train a random Forrest Classifier on Features
        if 'seed' in kwargs:
            np.random.seed(**specificKwargs(kwargs, {'seed': 1}))
        for _, bchar in self.outlierBlocks:
            if bchar[1] not in self.surrogates:
                self.surrogates[bchar[1]] = sklearn.ensemble.RandomForestClassifier(**specificKwargs(kwargs, {'n_estimators': 500}))
                self.surrogates[bchar[1]].fit(self.getDataframe(bchar[1], adjustedToOutlierBlock = adjustedToOutlierBlock),
                             self.npmap({True: 'outlier', False: 'inlier'})(self.getOutlierAdjusted(adjustedToOutlierBlock=adjustedToOutlierBlock)))
                log(f'Surrogates for len {bchar[1]} trained')
    
    def fitLime(self, adjustedToOutlierBlock=False, **kwargs):
        if len(self.surrogates) == 0:
            self.fitSurrogate(**kwargs)
        for _, bchar in self.outlierBlocks:
            if bchar[1] not in self.lime:
                preddf = self.getDataframe(bchar[1], adjustedToOutlierBlock=adjustedToOutlierBlock)
                self.lime[bchar[1]] = lime.lime_tabular.LimeTabularExplainer(preddf.values,
                                                                 feature_names=preddf.columns.values,
                                                                 discretize_continuous=True,
                                                                 class_names=self.surrogates[bchar[1]].classes_)

    def checkFitSurrogate(self):
        # if len(self.surrogates) == 0:
        self.fitSurrogate()

    def fitShap(self, adjustedToOutlierBlock = False, **kwargs):
        self.checkFitSurrogate()
        for _, bchar in self.outlierBlocks:
            if bchar[1] not in self.shap:
                self.shap[bchar[1]] = shap.TreeExplainer(self.surrogates[bchar[1]])
    
    def fitExplainers(self, adjustedToOutlierBlock = False, **kwargs):
        self.fitLime(adjustedToOutlierBlock=adjustedToOutlierBlock, **kwargs)
        self.fitShap(adjustedToOutlierBlock=adjustedToOutlierBlock, **kwargs)
        self.fitContrastiveFoil(adjustedToOutlierBlock=adjustedToOutlierBlock)
     
    def fitContrastiveFoil(self, adjustedToOutlierBlock = False, **kwargs):
        self.checkFitSurrogate()
        for _, bchar in self.outlierBlocks:
            if bchar[1] not in self.cfoil:
                preddf = self.getDataframe(bchar[1], adjustedToOutlierBlock=adjustedToOutlierBlock)
                dm = ce.domain_mappers.DomainMapperTabular(preddf.values, feature_names=preddf.columns.values, contrast_names=self.surrogates[bchar[1]].classes_)
                self.cfoil[bchar[1]] = ce.ContrastiveExplanation(dm, **specificKwargs(kwargs, {'verbose': False}))
    
    def getOutlierBlockLengthOfInstance(self, instanceIndex, adjustedToOutlierBlock = False):
        bl, bchar = [b for b in self.consecBlocks if instanceIndex in range(*b[0])][0]
        if ~bchar[0]:
            bl, bchar = self.outlierBlocks[np.argmin([b[1] for _, b in self.outlierBlocks])]
            print('Careful. I dont have a surrogate for inliers. So I will pick the smallest window length available: {}'.format(bchar[1]))
        instance = self.getDataframe(bchar[1], adjustedToOutlierBlock=adjustedToOutlierBlock).iloc[instanceIndex, :]
        return bl, bchar, instance
    
    def explainLimeInstance(self, instanceIndex, adjustedToOutlierBlock = False, mapExplain = True, **kwargs):
        if len(self.lime) == 0:
            self.fitLime()
        _, bchar, instance = self.getOutlierBlockLengthOfInstance(instanceIndex)
        explanation = self.lime[bchar[1]].explain_instance(instance.values, self.surrogates[bchar[1]].predict_proba, **specificKwargs(kwargs, {'num_features': 5}))
        if mapExplain:
            feat_cols = self.getDataframe(bchar[1]).columns.tolist()
            explanation = explanation.as_map()
            explanation = {i: [(feat_cols[c[0]], c[1]) for c in explanation[i]] for i in explanation}
        return explanation
    
    def explainShapInstance(self, instanceIndex, adjustedToOutlierBlock = False, plot=False, **kwargs):
        if len(self.shap) == 0:
            self.fitShap()
        _, bchar, instance = self.getOutlierBlockLengthOfInstance(instanceIndex)
        shap_values = self.shap[bchar[1]].shap_values(instance.values)
        if plot:
            exp = (self.shap[bchar[1]].expected_value[0], shap_values[0], np.float64(instance.values))
            return exp
        return shap_values
    
    def explainContrastiveFoilInstance(self, instanceIndex, **kwargs):
        if len(self.cfoil) == 0:
            self.fitContrastiveFoil()
        _, bchar, instance = self.getOutlierBlockLengthOfInstance(instanceIndex)
        if 'domain' in kwargs and specificKwargs(kwargs, {'domain':True})['domain']:
            exp = self.cfoil[bchar[1]].explain_instance_domain(self.surrogates[bchar[1]].predict_proba, instance)
        else:
            exp = self.cfoil[bchar[1]].explain_instance(self.surrogates[bchar[1]].predict_proba, instance)
        #exp = self.__cfoil.explain_instance_domain(self.__surrogate.predict_proba, instance.iloc[1:])
        return exp

    def explainAll(self, index):
        ob = self.outlierBlocks
        index = index % len(ob)
        index = ob[index]
        index = index[0][0] + (index[1][1] // 2)
        exp=[]
        exp.append(self.explainLimeInstance(index))
        log(exp[0])
        exp.append(self.explainShapInstance(index))
        log(exp[1])
        exp.append(self.explainContrastiveFoilInstance(index))
        log(exp[2])
        return exp

    '''
    def plotOutlierDistributionConsecutive(self, figAxTup = None, **kwargs):
        fig, ax = plt.subplots(1,1, **specificKwargs(kwargs, {'figsize': self.__figsize})) if figAxTup == None else figAxTup
        #x = self.data.bare_dataframe[[self.data.column_sort]]
        y = self.data.bare_dataframe.drop(columns=[self.data.column_sort, self.data.column_id])
        labels = []
        handles = [None] * 4
        for ind, (area, areatype) in enumerate(self.consecBlocks):
            labels.append(['i','o'][int(areatype[0])])
            if areatype[1] > 1:
                bp = ax.boxplot(y.values[range(*area)], positions=[ind], patch_artist = True)
                bp['boxes'][0].set(facecolor=['blue','red'][int(areatype[0])])
                handles[int(areatype[0])] = bp['boxes'][0]
            else:
                handles[int(areatype[0]) + 2] = ax.scatter(x=[ind], y=y.values[range(*area)], marker='x', color = ['blue','red'][int(areatype[0])])
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels)
        labs = ('inlier (i)', 'outlier (o)', 'inlier', 'outlier')
        h = (tuple([handle for handle in handles if handle != None]), tuple([labs[i] for i,ha in enumerate(handles) if ha != None]))
        ax.legend(h[0], h[1], **specificKwargs(kwargs, {'loc':'lower right','fontsize': self.__fontsize}))
        return fig, ax
    
    
    
    
    def outlierBlockExplanation(self, bInd = 0, maxFeatures=3, **kwargs):
        blocks = self.outlierBlocks
        bl, bchar = blocks[bInd]
        
        # Gather explanations for all outlier instances
        exp = [self.explainLimeInstance(instanceIndex = i) for i in range(*bl)]
        # Find explained features
        expmap = np.array([e[0] for i in range(len(exp)) for e in exp[i].as_map()[1]])
        # Get unique list of explained features and count their occurances in all outlier instances
        expun = np.unique(expmap.reshape(-1, len(exp[0].as_map()[1])), return_counts=True)
        # Find the top <maxFeatures> important features
        expun = expun[0][list(reversed(np.argsort(expun[1], axis=0)))][:min(len(expun[0]), maxFeatures)]
        # Find the textual representation
        expop = np.array([e for i in range(len(exp)) for e in exp[i].as_list()]).reshape(-1, len(exp[0].as_list()) * 2)#, return_counts=True)
        # Match the feature map to the textual representation
        exp = np.array(list(zip(expmap, expop.reshape(-1,2)))).reshape(-1,len(exp[0].as_map()[1]),2)
        exp = np.array([np.array([np.array([i[0], i[1][0], i[1][1]]) for i in t if i[0] in expun]) for t in exp[:,:,:]])
        #Put the results into a dictionary for easier use
        expDict = np.array([{int(i[0]): i[1:] for i in t} for t in exp])
        
        return expDict, exp, expun
    
    def plotRelevantFeaturesMatrix(self, minOutliersConsecutive = 2, topmotifs = 2, maxFeatures=3):
        tsid = 0
        fsz = 16
        #fsz = self.__fontsize
        cdf = self.data.bare_dataframe[self.data.bare_dataframe[self.data.column_id] == tsid]
        blocks = self.outlierBlocks
        fig = plt.figure(figsize=(30,20 * len(blocks)))
        #print('Showing the outlier subseries found, with len >= {:.0f} compared to the top {} motifs of same length'.format(percentage*self.data.windowsize, topmotifs))
        grid = plt.GridSpec(1 + len(blocks) * (maxFeatures), (topmotifs + 1) * 2, hspace= .2, wspace = .2)
        main_ax = fig.add_subplot(grid[0,:])
        x = cdf[self.data.column_sort].values
        y = cdf.drop(columns = [self.data.column_id, self.data.column_sort])
        y_adj = y.copy()
        c = lambda x: plt.cm.Reds(mpl.colors.Normalize(vmin=-1, vmax=len(blocks))(x))
        noBorders = lambda axis, borders = ['top', 'bottom', 'left', 'right']: list(map(lambda x: axis.spines[x].set_visible(False), borders))
        y_adj.iloc[[x for bl, bc in blocks for x in list(range(*bl))],:] = np.nan
        main_ax.plot(x, y_adj, color='black', label = 'original data')
        main_ax.set_title('Original data and found outlier subseries for {}'.format(''), fontsize = fsz)
        share_ax1 = main_ax
        for bInd, (bl, bchar) in log_progress(enumerate(blocks), every=1, name = 'Block'):
            x_pred = self.featureFrames[bchar[1]][self.data.column_sort].values + bchar[1] // 2
            bl2 = (bl[0] - 1, bl[1] + 1)
            main_ax.plot(x[range(*bl2)], y.iloc[slice(*bl2)], color = 'red')
            bl = (bl[0] - bchar[1] // 2, bl[1] - bchar[1] // 2)
            bl2 = (bl2[0] - bchar[1] // 2, bl2[1] - bchar[1] // 2)
            expDict, exp, expun = self.outlierBlockExplanation(bInd, maxFeatures = maxFeatures)
            for ind, eu in enumerate(expun):
                eu = int(eu)
                cur_ax = fig.add_subplot(grid[len(blocks)*bInd + bInd + 1 + ind, :])
                share_ax1.get_shared_x_axes().join(share_ax1, cur_ax)
                y_predadj = self.featureFrames[bchar[1]].drop(columns=[self.data.column_sort, self.data.column_id]).iloc[:, eu].values
                y_predadj[range(*bl)] = np.nan
                cur_ax.plot(x_pred,
                            y_predadj, color = 'blue')
                cur_ax.plot(x_pred[range(*bl2)], self.featureFrames[bchar[1]].drop(columns=[self.data.column_sort, self.data.column_id]).iloc[slice(*bl2), eu], color = 'red')
                cur_ax.set_title(self.featureFrames[bchar[1]].drop(columns=[self.data.column_sort, self.data.column_id]).columns.values[eu])
        
        whole_ax = fig.add_subplot(grid[:,:], xticks=[], yticks=[])
        whole_ax.patch._facecolor = (.9,.9,.9,.2)
        noBorders(whole_ax)
        share_ax1.get_shared_x_axes().join(share_ax1, whole_ax)
        for bInd, (bl, bchar) in enumerate(blocks):
            x_pred = self.featureFrames[bchar[1]][self.data.column_sort].values
            whole_ax.axvline(x[bl[0]], color = 'red', alpha= .4, zorder = 100)
            whole_ax.axvline(x[bl[1]], color = 'red', alpha= .4, zorder = 100)
    
    def matrixProfilePlot(self):
        tsid = 0
        i = 8
        topmotifs = 3
        fsz = 16
        # Get the current combination
        cdf = self.data.bare_dataframe[self.data.bare_dataframe[self.data.column_id] == tsid]
        #x,y,out,outliers,colname = getCombination(i)
        x = cdf[self.data.column_sort].values
        y = cdf.drop(columns = [self.data.column_id, self.data.column_sort]).values.flatten()
        # Get the consecutive subseries of same category
        blocks = self.consecBlocks
        # Only get the subseries which are outliers and have a percentage (=50) % length of windowsize (=30)
        outblocks = self.outlierBlocks
        # Define cholorscheme for outliers
        c = lambda x: plt.cm.Reds(mpl.colors.Normalize(vmin=-1, vmax=len(outblocks))(x))
        noBorders = lambda axis, borders = ['top', 'bottom', 'left', 'right']: list(map(lambda x: axis.spines[x].set_visible(False), borders))

        fig = plt.figure(figsize=(30,20 * len(outblocks)))
        print('Showing the outlier subseries found compared to the top {} motifs of same length'.format(topmotifs))
        grid = plt.GridSpec(1 + len(outblocks) * 4, (topmotifs + 1) * 2, hspace= .2, wspace = .2)
        main_ax = fig.add_subplot(grid[0,:])
        y_adj = y.copy()
        y_adj[[x for bl, bc in outblocks for x in list(range(bl[0] + 1, bl[1] - 1))]] = np.nan
        main_ax.plot(x, y_adj, color='black', label = 'original data')
        main_ax.set_title('Original data and found outlier subseries', fontsize = fsz)
        for bInd, (bl, bchar) in enumerate(outblocks):
            bl2 = (bl[0] - 1, bl[1] + 1)
            motiflen = bchar[1]
            xo = x[range(*bl)]
            yo = y[range(*bl)]
            ysub_adj = y.copy()
            ysub_adj[range(bl[0] + 1, bl[1] - 1)] = np.nan
            main_ax.plot(x[range(*bl)], y[range(*bl)], color=c(bInd), label = 'Outlier subseries')
            rInd = 4 * bInd + 3

            border0 = fig.add_subplot(grid[rInd-2:rInd+2, :], xticks =[], yticks = [])
            border1 = fig.add_subplot(grid[rInd:rInd+2, 0:2], xticks =[], yticks = [])
            border1.set_title('Outlier subseries of length {}'.format(motiflen), fontsize = fsz)
            cur_ax1 = fig.add_subplot(grid[rInd, 0:2])
            cur_ax1.plot(xo, yo, color=c(bInd))
            cur_ax2 = fig.add_subplot(grid[rInd + 1, 0:2])
            bpo = cur_ax2.boxplot(yo)
            cur_ax2.set_title('Distribution of subseries', fontsize=fsz)
            border2 = fig.add_subplot(grid[rInd:rInd+2, 2:], xticks =[], yticks = [])
            border2.set_title('Corresponding top {} motifs derived by MP with length {}'.format(topmotifs, motiflen), fontsize=fsz)

            submain_ax = fig.add_subplot(grid[rInd-2, :], xticks=[])
            mp_ax = fig.add_subplot(grid[rInd-1,:])
            mp_ax.set_title('Matrix profile for length {} motifs'.format(motiflen), fontsize=fsz)
            submain_ax.plot(x, ysub_adj, color = 'black', label = 'original data')
            submain_ax.plot(xo, yo, color = c(bInd), label = 'outlier data')
            submain_ax.legend()
            noBorders(submain_ax, ['bottom'])
            noBorders(mp_ax, ['top'])

            share_ax1 = cur_ax1
            share_ax2 = cur_ax2

            print(y.shape, motiflen)
            mp = matrixProfile.stomp(y, motiflen)
            mt, mtd = motifs.motifs(y, mp, max_motifs=topmotifs)
            mp_adj = np.append(mp[0],np.zeros(motiflen-1)+np.nan)

            mp_ax.plot(x, mp_adj, color = 'lightblue', label = 'matrix profile')

            for moti, (mot, motd) in enumerate(zip(mt, mtd)):
                slices = [slice(m, m+bchar[1], 1) for m in mot]
                intersections = [np.intersect1d(np.arange(*bl), y) for y in [np.arange(s.start, s.stop) for s in slices]]
                ymo = np.array([y[s] for s in slices])
                xmo = np.array([x[s] for s in slices])
                m_ax1 = fig.add_subplot(grid[rInd, 2 + moti*2: 4 + moti*2])
                m_ax1.patch._facecolor = (.9,.9,.9,.2)
                #m_ax1.spines['right'].set_visible(False)
                #m_ax1.spines['left'].set_visible(False)
                share_ax1.get_shared_y_axes().join(share_ax1, m_ax1)
                mcm = lambda x: plt.cm.Greens_r(mpl.colors.Normalize(vmin=-1, vmax=ymo.shape[0]+1)(x))
                isctcm = lambda x: plt.cm.Reds(mpl.colors.Normalize(vmin=-1, vmax=ymo.shape[0]+1)(x))
                for row in range(ymo.shape[0]):
                    curcol = mcm(row)
                    cury = ymo[row,:]
                    curx = xmo[row,:]
                    if intersections[row].size != 0:
                        zorder = 20
                        subslice = [sl in intersections[row] for sl in np.arange(slices[row].start, slices[row].stop)]
                        m_ax1.plot(xo, cury, color = 'black', lw=1, zorder = zorder)
                        m_ax1.plot(xo[subslice], cury[subslice], lw=2, color = 'red', zorder = zorder)
                        submain_ax.plot(curx, cury, color = 'y', lw=1, zorder = zorder)
                        submain_ax.plot(curx[subslice], cury[subslice], lw=2, color = 'red', zorder = zorder)
                    else:
                        zorder = 9
                        m_ax1.plot(xo, cury, color = curcol, zorder = zorder)
                        submain_ax.plot(curx, cury, color = curcol)
                m_ax2 = fig.add_subplot(grid[rInd + 1, 2 + moti*2: 4 + moti*2])
                m_ax2.patch._facecolor = (.9,.9,.9,.2)
                #m_ax2.spines['top'].set_visible(False)
                m_ax2.set_title('Motif-dist with dist {:2.2f}{}'.format(motd,
                        '' if moti != (len(mt) - 1) else ' (max = {:2.2f})'.format(max(mp[0]))), fontsize=fsz)
                share_ax2.get_shared_y_axes().join(share_ax2, m_ax2)
                bp = m_ax2.boxplot(ymo.transpose(), patch_artist=True)
                for bpi, bpl in enumerate(bp['boxes']):
                    if intersections[bpi].size != 0:
                        bpl.set(facecolor='red')
                    else:
                        bpl.set(facecolor=mcm(bpi))
                share_ax1 = m_ax1
                share_ax2 = m_ax2

            allmotifs_ax = fig.add_subplot(grid[rInd + 1, 1:], xticks = [], yticks=[])
            noBorders(allmotifs_ax)
            share_ax1.get_shared_y_axes().join(share_ax2, allmotifs_ax)
            allmotifs_ax.axhline(bpo['medians'][0]._y[0], c= bpo['medians'][0]._color)
            allmotifs_ax.axhline(bpo['whiskers'][0]._y[1], c= 'lightgrey', alpha = .7)
            allmotifs_ax.axhline(bpo['whiskers'][1]._y[1], c= 'lightgrey', alpha = .7)
            allmotifs_ax.axhline(max(bpo['boxes'][0]._y), c= 'lightgrey', alpha = .7)
            allmotifs_ax.axhline(min(bpo['boxes'][0]._y), c= 'lightgrey', alpha = .7)
            allmotifs_ax.patch.set_alpha(0)
        main_ax.legend()

'''