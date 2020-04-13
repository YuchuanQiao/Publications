# -------------------------------------------------------------------------------
# this is a python script for the SPRAED image experiment
# change parameter settings for the evaluation of different parameter, such as regularization tau, kappa, number of samples for preconditoner estimation.
# 03-15-2018

import os
import sys
import os.path
import glob

# directory of the experiment
machineDir = ""
dataDir = "FPSGD/data/SPREAD/mhd"
resultDir = os.path.join(machineDir, "results", "FPSGD", "SPREAD")
ParafilePath = "FPSGD/Scripts/SPREAD/Parameters"
# timing
excutablePath = "tools/elastix/bin_linux/bin"

elastix = os.path.join(excutablePath, "elastix")
transformix = os.path.join(excutablePath, "transformix")
groundtruthDir = "FPSGD/data/SPREAD/groundtruth/distinctivePoints"
t0Dir = 'FPSGD/results/SPREAD'


def ChangeParameterFile(baseParameterFile="", parameter="", experimentName="", expType="", iterationNum="",
                        transformType="", metricName="", regularPercentile="", conditionNumber=""):
    searchExp1 = '(Optimizer "PreconditionedStochasticGradientDescent")'
    replaceExp1 = '(Optimizer "PreconditionedGradientDescent")'
    replaceExp12 = '(Optimizer "AdaptiveStochasticGradientDescent")'

    searchExp2 = '(ShowExactMetricValue "false")'
    replaceExp2 = '(ShowExactMetricValue "true")'

    searchExp3 = '(MaximumNumberOfIterations 500)'
    replaceExp3 = searchExp3.replace('500', iterationNum)

    searchExp4 = '(Transform "BSplineTransform")'
    replaceExp4 = searchExp4.replace('BSpline', transformType)

    searchExp5 = '(Metric "AdvancedMeanSquares")'
    replaceExp5 = '(Metric "AdvancedMattesMutualInformation")'
    replaceExpNC = '(Metric "AdvancedNormalizedCorrelation")'
    replaceExpNMI = '(Metric "NormalizedMutualInformation")'

    searchExp6 = '(RegularizationKappa 0.9)'
    replaceExp6 = searchExp6.replace('0.9', regularPercentile)

    searchExp7 = '(JacobiTypePreconditioner "true")'
    replaceExp7 = '(JacobiTypePreconditioner "false")'
    searchExp8 = '(ConditionNumber 2.0)'
    replaceExp8 = searchExp8.replace('2.0', conditionNumber)
    searchExp9 = '(MaximumStepLengthRatio 1.0)'
    replaceExp9 = '(MaximumStepLengthRatio 1.0)'

    if experimentName == 'FPSGD':
        replaceExp1 = searchExp1
    elif experimentName == 'FASGD':
        replaceExp1 = replaceExp12
    elif experimentName == 'PSGD':
        replaceExp1 = replaceExp1
    elif experimentName == 'PSGD-J':
        replaceExp7 = searchExp7
        replaceExp1 = searchExp1
        replaceExp9 = replaceExp9.replace('1.0', '0.1')

    if expType == 'Timing':
        replaceExp2 = searchExp2
    if metricName == 'MSD':
        replaceExp5 = searchExp5
    elif metricName == 'NC':
        replaceExp5 = replaceExpNC
    elif metricName == 'NMI':
        replaceExp5 = replaceExpNMI

    with open(parameter, 'w') as fout:
        with open(baseParameterFile) as fin:
            for line in fin:
                if searchExp1 in line:
                    line = line.replace(searchExp1, replaceExp1)
                if searchExp2 in line:
                    line = line.replace(searchExp2, replaceExp2)
                if searchExp3 in line:
                    line = line.replace(searchExp3, replaceExp3)
                if searchExp4 in line:
                    line = line.replace(searchExp4, replaceExp4)
                if searchExp5 in line:
                    line = line.replace(searchExp5, replaceExp5)
                if searchExp6 in line:
                    line = line.replace(searchExp6, replaceExp6)
                if searchExp7 in line:
                    line = line.replace(searchExp7, replaceExp7)
                if searchExp8 in line:
                    line = line.replace(searchExp8, replaceExp8)
                if searchExp9 in line:
                    line = line.replace(searchExp9, replaceExp9)
                fout.write(line)


def SPREAD_registration(fixed="", moving="", parameter="", outputName="", t0="", defile="", threadsNum=""):

    # print ("Step 1: run elastix")
    if t0 == '':
        cmdStr = "%s -f %s -m %s -out %s -p %s -threads %s" % \
                 (elastix, fixed, moving, outputName, parameter, threadsNum)
    else:
        cmdStr = "%s -f %s -m %s -out %s -p %s -t0 %s -threads %s" % \
                 (elastix, fixed, moving, outputName, parameter, t0, threadsNum)
    print(cmdStr)
    if not os.path.exists(os.path.join(outputName, 'transformix.log')):
        os.system(cmdStr)
    #
    tpfile = os.path.join(outputName, "TransformParameters.0.txt")
    # if os.path.exists(tpfile):
    cmdStr = "%s -def %s -out %s -tp %s" % \
             (transformix, defile, outputName, tpfile)
    print(cmdStr)
    os.system(cmdStr)


def SPREAD_TABLE2():
    data_path = ['p000_Aard', 'p001_Beer', 'p003_Eede', 'p005_Halt', 'p006_Harr', 'p007_Klei', 'p008_Mier', 'p009_Neuv',
                 'p011_Nijs', 'p012_Pete', 'p013_Raad', 'p014_Rove', 'p017_Sloe', 'p018_Sloo', 'p019_Stok', 'p020_Sunn',
               'p021_Wilt', 'p023_Wout', 'p024_Zee']

    # expTypeList =['Convergence']
    expTypeList = ['Timing']
    iterationNum = '500'
    transformType = 'BSpline'
    # transformType = 'Affine'
    conditionNumerList = ['1', '2', '8', '16']
    # conditionNumerList = ['4']
    metric = ["MSD"]

    # experimentName = ['FASGD']
    experimentName = ['FPSGD']
    # experimentName = ['PSGD-J']
    # experimentName = ['PSGD-J','FASGD','FPSGD']

    # this convergence script is expected to run on grid server.
    FPSGD_convergence_exp_script = 'FPSGD_convergence_exp_script.txt'
    with open(FPSGD_convergence_exp_script, 'w') as fout:
        for expType in expTypeList:
            if expType == 'Timing':
                threadsNum = '12'
            else:
                threadsNum = '6'
            for exp in experimentName:
                # determine the method
                if exp == 'FPSGD':
                    regularizationRange = 11
                else:
                    regularizationRange = 1
                for num in range(6, 7, 2):
                    # obtain the regularPercentile
                    regularPercentile = str(float(num) / 10)
                    for kappa in conditionNumerList:
                        for metricName in metric:
                            # for elastix parameter file
                            out = exp + '_' + '%02d' % (
                            num) + '_Iteration' + iterationNum + '_' + expType + '_ConditionNumber' + kappa + '_Threads' + threadsNum

                            parameterFileName = 'parameters_' + metricName + '_' + transformType + '_' + out + '.txt'
                            parameter = os.path.join(ParafilePath, parameterFileName)
                            if transformType == 'Affine':
                                baseParameterFile = os.path.join(ParafilePath, 'baseParameterFileForFPSGDExpSPREADR0')
                            else:
                                baseParameterFile = os.path.join(ParafilePath,
                                                                 'baseParameterFileForFPSGDExp')
                            ChangeParameterFile(baseParameterFile, parameter, exp, expType, iterationNum, transformType,
                                                metricName, regularPercentile, kappa)

                            for par in data_path:
                                # elastix experiment process unit
                                # specify the experiment parameters

                                fixed = os.path.join(dataDir, par, "baseline_1_crop.mha")
                                moving = os.path.join(dataDir, par, "followup_1_crop.mha")
                                outputName = os.path.join(resultDir, metricName, transformType, out, par)
                                defile = os.path.join(groundtruthDir, par[0:4] + "_baseline_1_Cropped_point.txt")
                                if transformType == 'Affine':
                                    t0 = ''
                                    cmdStr = "%s -f %s -m %s -out %s -p %s -threads %s" % \
                                             (elastix, fixed, moving, outputName, parameter, threadsNum)
                                else:
                                    t0 = os.path.join(t0Dir, "MI", "OriginalASGD_Affine", par,
                                                      "TransformParameters.0.txt")
                                    cmdStr = "%s -f %s -m %s -out %s -p %s -t0 %s -threads %s" % \
                                             (elastix, fixed, moving, outputName, parameter, t0, threadsNum)
                                qsubStr = 'echo \'' + cmdStr + '\' | qsub -q compute.q -pe smp 8:16 -N ' + out + par +'\n'
                                fout.write(qsubStr)
                                if os.path.exists(outputName) == False:
                                    os.makedirs(outputName)

                                SPREAD_registration(fixed=fixed, moving=moving, parameter=parameter, outputName=outputName,
                                                    t0=t0,
                                                    defile=defile, threadsNum=threadsNum)

if __name__ == "__main__":
    SPREAD_TABLE2()
