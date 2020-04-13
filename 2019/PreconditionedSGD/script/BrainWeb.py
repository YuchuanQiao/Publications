# -------------------------------------------------------------------------------
# this is a python script for the BrainWeb image experiment
# for FPSGD test
# experiments on FPSGD
#
# 03-15-2018

import os
import sys
import os.path
import glob

# directory of the experiment
machineDir = ""
dataDir = "/data/BrainWeb"

resultDir = os.path.join(machineDir, "results", 'FPSGD', "BrainWeb")
ParafilePath = "Parameters"

excutablePath = "tools/elastix/bin_linux/bin"
elastix = os.path.join(excutablePath, "elastix")
transformix = os.path.join(excutablePath, "transformix")

fixedImage = 't2_normal'
movingImage = 't1_normal'
fixedImagePath = os.path.join(dataDir, 't1t2', fixedImage + '.mhd')
movingImagePath = os.path.join(dataDir, 't1t2', movingImage + '.mhd')

fixedMaskpath = os.path.join(dataDir, 't1t2_mask', 'maskt1_normal.mhd')
deformationPath = os.path.join(dataDir, 'DeformationWithinMask')
deformationList = [f for f in os.listdir(deformationPath) if f.endswith("param.txt")]


def ChangeParameterFile(baseParameterFile="", parameter="", experimentName="", expType="", iterationNum="",
                        transformType="", metricName="", regularPercentile="", conditionNumber=""):
    searchExp1 = '(Optimizer "PreconditionedStochasticGradientDescent")'
    replaceExp1 = '(Optimizer "PreconditionedGradientDescent")'
    replaceExp12 = '(Optimizer "AdaptiveStochasticGradientDescent")'
    replaceExp13 = '(Optimizer "StochasticGradientDescentMachineLearning")'

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
    elif experimentName == 'PSGD_ML':
        replaceExp1 = replaceExp13
        replaceExp9 = replaceExp9.replace('1.0', '0.00001')

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


def do_registration(fixed="", moving="", fmask="", parameter="", outputName="", t0="", defile="", threadsNum=""):
    if os.path.exists(outputName) == False:
        os.makedirs(outputName)

    print ("Step 1: run elastix")
    if t0 == '':
        cmdStr = "%s -f %s -m %s -out %s -p %s -threads %s" % \
                 (elastix, fixed, moving, outputName, parameter, threadsNum)
    else:
        cmdStr = "%s -f %s -fMask %s -m %s -out %s -p %s -t0 %s -threads %s" % \
                 (elastix, fixed, fmask, moving, outputName, parameter, t0, threadsNum)
    print(cmdStr)
    if not os.path.exists(os.path.join(outputName, 'elastix.log')):
        os.system(cmdStr)


def BrainWeb():
    expTypeList = ['Timing']
    # expTypeList = ['Convergence']
    iterationNum = '1000'
    transformType = 'BSpline'
    metric = ["MI"]
    conditionNumerList = ['4']
    experimentName = ['PSGD-J', 'FASGD', 'FPSGD','PSGD_ML']
    # experimentName = ['PSGD_ML']

    FPSGD_convergence_exp_script = 'FPSGD_convergence_exp_script.txt'
    with open(FPSGD_convergence_exp_script, 'w') as fout:
        for expType in expTypeList:
            if expType == 'Timing':
                threadsNum = '12'
            else:
                threadsNum = '4'
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
                            out = exp + '_' + '%02d' % (
                                num) + '_Iteration' + iterationNum + '_' + expType + '_ConditionNumber' + kappa + '_Threads' + threadsNum
                            parameterFileName = 'BrainWeb_parameters_' + metricName + '_' + transformType + '_' + out + '.txt'
                            parameter = os.path.join(ParafilePath, parameterFileName)
                            baseParameterFile = os.path.join(ParafilePath, 'baseParameterFileForFPSGDExpBrainWebR0')
                            ChangeParameterFile(baseParameterFile, parameter, exp, expType, iterationNum, transformType,
                                                metricName, regularPercentile, kappa)
                            for t0_name in deformationList:
                                deformationParm = t0_name.split('.txt')[0]
                                t0 = os.path.join(deformationPath, t0_name)
                                outputName = os.path.join(resultDir, metricName, transformType, out, deformationParm)
                                if os.path.exists(outputName) == False:
                                    os.makedirs(outputName)
                                if t0 == '':
                                    cmdStr = "%s -f %s -m %s -out %s -p %s -threads %s" % \
                                             (elastix, fixedImagePath, movingImagePath, outputName, parameter,
                                              threadsNum)
                                else:
                                    cmdStr = "%s -f %s -fMask %s -m %s -out %s -p %s -t0 %s -threads %s" % \
                                             (elastix, fixedImagePath, fixedMaskpath, movingImagePath, outputName,
                                              parameter, t0, threadsNum)

                                qsubStr = 'echo \'' + cmdStr + '\' | qsub -q compute.q -N ' + out + deformationParm + '\n'

                                fout.write(qsubStr)

                                # run the experiment.
                                do_registration(fixed=fixedImagePath, fmask=fixedMaskpath, moving=movingImagePath,
                                                parameter=parameter, outputName=outputName,
                                                t0=t0,
                                                threadsNum=threadsNum)


if __name__ == "__main__":
    BrainWeb()
