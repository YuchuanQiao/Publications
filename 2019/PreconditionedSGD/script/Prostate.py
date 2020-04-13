# -------------------------------------------------------------------------------
# this is a python script for the Prostate image experiment
# with MI,BSpline
# 11-02-2016
# !/usr/bin/python

import os
import sys
import os.path
import glob
import re
import threading
# import CalculateSurfaceDistance as CSD
# import numpy
import shutil
import time
import subprocess

# directory of the experiment
machineDir = ""
dataDir = "/data/Prostate/ProstatePatient"
resultDir = os.path.join(machineDir, "results", "FPSGD", "Prostate", "Cropped")
ParafilePath = "/Scripts/VoxelwisedASGD/Parameters"
fullImageSizeDir = os.path.join(machineDir, "results", "FPSGD", "Prostate", "NC_fullImage")
excutablePath = "tools/elastix/bin_linux/bin"
# excutablePath = "tools/elastix/bin_linux_GPU/bin"

elastix = os.path.join(excutablePath, "elastix")
transformix = os.path.join(excutablePath, "transformix")

itkToolsDir = 'tools/ITKTools/bin/bin'
pxcomputeoverlap = os.path.join(itkToolsDir, "pxcomputeoverlap")


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
    # replaceExp9 = '(MaximumStepLengthRatio 0.00001)' # for AdaGrad
    # replaceExp9 = '(MaximumStepLengthRatio 0.1)' # for PSGD-J
    replaceExp9 = '(MaximumStepLengthRatio 1.0)' # for PSGD-J


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


def Prostate_registration(metric, fixedImage, movingImage, fixedSegmentation, movingSegmentation,
                        fixedSegmentationVtk, movingSegmentationVtk, outDir, organName,
                        parameter, t0, fullImageSizeInputDir, threadsNum):
    # parameter files

    outputName = os.path.join(outDir, "OriginalImage")
    if not os.path.exists(outputName):
        os.makedirs(outputName)

    elastix_flag = False
    print ("Step 1: run elastix")
    if t0 == '':
        cmdStr = "%s -f %s -m %s -out %s -p %s -threads %s" % \
                 (elastix, fixedImage, movingImage, outputName, parameter, threadsNum)
    else:
        cmdStr = "%s -f %s -m %s -out %s -p %s -t0 %s -threads %s" % \
                 (elastix, fixedImage, movingImage, outputName, parameter, t0, threadsNum)
    print(cmdStr)
    elastixlogfile = os.path.join(outputName, "elastix.log")
    if not os.path.isfile(elastixlogfile):
        os.system(cmdStr)

    organFolder = os.path.join(outDir, organName)
    if not os.path.exists(organFolder):
        os.makedirs(organFolder)
    outputFileName = os.path.join(organFolder, "overlap.txt")
    diceOverlapCheck = True
    if os.path.isfile(os.path.join(outputName, 'TransformParameters.0.txt')):
        if os.path.isfile(outputFileName):
            with open(outputFileName, 'r') as fin:
                for fline in fin:
                    if 'Overlap:' in fline:
                        # if overlap result is in the file, check is canceled
                        diceOverlapCheck = False
                    else:
                        pass
        if diceOverlapCheck:
            # transform the sgementation image and calculate the Dice overlap
            evaluateDiceOverlap(outputName, organFolder, outputFileName, fullImageSizeInputDir)
    else:
        print(os.path.join(outputName, 'TransformParameters.0.txt') + ' is not exist.')


def evaluateDiceOverlap(outputName="", organFolder="", outputFileName="", fullImageSizeInputDir=''):
    mhatransformixFlag = True
    transformixlogfile = os.path.join(organFolder, "transformix.log")
    resultOfOrganTransform = os.path.join(organFolder, "result.mha")
    copyImageInfoToTransformParameterFile(os.path.join(fullImageSizeInputDir, "OriginalImage"), outputName)
    replaceSplineOrder(os.path.join(outputName, 'TransformParameters.0.txt'))
    if not os.path.isfile(resultOfOrganTransform):
        print ("Step 2: run transformix")
        cmdStr = "%s -in %s -out %s -tp %s" % \
                 (transformix, movingSegmentation, organFolder,
                  os.path.join(outputName, 'TransformParameters.0.seg.txt'))
        os.system(cmdStr)
    # compute the overlap of transformation result
    # and segmentation image of fixed image
    if not os.path.isfile(outputFileName):
        computeDSC(resultOfOrganTransform, fixedSegmentation, outputFileName)
        # os.remove(resultOfOrganTransform)


def computeDSC(input1, input2, output):
    print ("ComputeDSC Step: run pxcomputeoverlap 1")
    cmdStr = "%s -in %s %s >> %s" % \
             (pxcomputeoverlap, input1,
              input2, output)
    print (cmdStr)
    if not os.system(cmdStr) == 0:
        print("pxcomputeoverlap 1 failed")

    print ("ComputeDSC Step: run pxcomputeoverlap 2")
    cmdStr = "%s -in %s %s -l >> %s" % \
             (pxcomputeoverlap, input1, input2, output)
    if not os.system(cmdStr) == 0:
        print("pxcomputeoverlap 2 failed")


def replaceSplineOrder(filePath):
    fileNameTmp = filePath.split('.txt')[0] + '.seg.txt'
    # if os.path.exists( fileNameTmp ) == False :
    #   os.rename(filePath, filePath+".orig")
    with open(filePath) as fin:
        with open(fileNameTmp, 'w') as fout:
            for line in fin:
                if "FinalBSplineInterpolationOrder 3" in line:
                    fout.write(line.replace('3', '0'))
                else:
                    fout.write(line)


def copyImageInfoToTransformParameterFile(inputTransformDir, outputTransformDir):
    print(inputTransformDir)
    for i in range(0, 1):
        transformOutput = os.path.join(outputTransformDir, "TransformParameters." + str(i) + ".txt")
        transformOutputTmp = os.path.join(outputTransformDir, "TransformParameters." + str(i) + "tmp.txt")
        shutil.copyfile(transformOutput, transformOutputTmp)
        transformInput = os.path.join(inputTransformDir, "TransformParameters." + str(i) + ".txt")
        with open(transformInput) as fcompare:
            for line in fcompare:
                if "(Size" in line:
                    size = line
                if "(Spacing" in line:
                    spacing = line
                if "(Origin" in line:
                    origin = line
        with open(transformOutputTmp) as fin:
            with open(transformOutput, 'w') as fout:
                for line in fin:
                    if "(Size" in line:
                        fout.write(line.replace(line, size))
                    elif "(Spacing" in line:
                        fout.write(line.replace(line, spacing))
                    elif "(Origin" in line:
                        fout.write(line.replace(line, origin))
                    else:
                        fout.write(line)


if __name__ == "__main__":
    startTime = time.clock()

    data_path = os.listdir(dataDir)
    patientNameList = sorted(data_path)
    print(patientNameList)
    metric = ["MI"]
    iterationNum = '200'
    # organs = ['SeminalVesicle','ITVsubSV','Bladder','Rectum']
    organs = ['GTV']
    # expTypeList = ['Convergence']
    expTypeList = ['Timing']
    transformType = 'BSpline'
    # t0 Affine/FASGD_00_Iteration500_Timing_ConditionNumber4
    # transformType = 'Affine'
    conditionNumerList = ['4']
    # experimentName = ['PSGD_ML','PSGD-J', 'FASGD', 'FPSGD']
    # experimentName = ['PSGD-J']
    experimentName = ['FASGD']

    FPSGD_convergence_exp_script = 'FPSGD_convergence_exp_script_bspline1.txt'
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
                            out = exp + '_' + '%02d' % (
                                num) + '_Iteration' + iterationNum + '_' + expType + '_ConditionNumber' + kappa + '_Threads' + threadsNum
                            parameterFileName = 'Prostate_parameters_' + metricName + '_' + transformType + '_' + out + '.txt'
                            parameter = os.path.join(ParafilePath, parameterFileName)
                            if transformType == 'Affine':
                                baseParameterFile = os.path.join(ParafilePath,
                                                                 'baseParameterFileForFPSGDExpProstateR0')
                            else:
                                baseParameterFile = os.path.join(ParafilePath,
                                                                 'baseParameterFileForFPSGDExp')
                            ChangeParameterFile(baseParameterFile, parameter, exp, expType, iterationNum, transformType,
                                                metricName, regularPercentile, kappa)

                            for patientNumIter in range(0, len(patientNameList)):
                                # go to the patient scan directory
                                patientScanDir = os.path.join(dataDir, patientNameList[patientNumIter])
                                # obtain the folder name of planning scan and following scans and array them
                                patientScanList = [f for f in os.listdir(patientScanDir) if
                                                   os.path.isdir(os.path.join(patientScanDir, f))]
                                patientScanList = sorted(patientScanList)  #

                                # for loop all scans in that patient
                                for i in range(0, len(patientScanList)):
                                    planningScanNum = 1
                                    # avoid the registrations between two same scans
                                    if i != planningScanNum:
                                        for organName in organs:
                                            # fixed image is the following scan and moving image is the planning scan
                                            fixedImage = os.path.join(patientScanDir, patientScanList[i], 'Images',
                                                                      'CroppedCTImageDilated.mha')
                                            movingImage = os.path.join(patientScanDir, patientScanList[planningScanNum],
                                                                       'Images', 'CroppedCTImageDilated.mha')
                                            movingSegmentation = os.path.join(patientScanDir,
                                                                              patientScanList[planningScanNum],
                                                                              'Contours_Cleaned', organName + '.mha')
                                            movingSegmentationVtk = os.path.join(patientScanDir,
                                                                                 patientScanList[planningScanNum],
                                                                                 'Contours_Cleaned', organName + '.vtk')

                                            fixedSegmentationPath = os.path.join(patientScanDir, patientScanList[i],
                                                                                 'Contours_Cleaned')
                                            fixedSegmentationNameList = [f for f in os.listdir(fixedSegmentationPath) if
                                                                         re.match(organName + '.mha', f)]
                                            fixedSegmentationVtkNameList = [f for f in os.listdir(fixedSegmentationPath)
                                                                            if re.match(organName + '.vtk', f)]
                                            if not fixedSegmentationNameList or not fixedSegmentationVtkNameList:
                                                print('There is no %s in this scan.') % organName
                                                continue
                                            else:
                                                fixedSegmentation = os.path.join(fixedSegmentationPath,
                                                                                 fixedSegmentationNameList[0])
                                                fixedSegmentationVtk = os.path.join(fixedSegmentationPath,
                                                                                    fixedSegmentationVtkNameList[0])

                                                patient_name = patientNameList[patientNumIter]

                                                patient_scan = patientScanList[i]

                                                outDir = os.path.join(resultDir, metricName, transformType, out,
                                                                      patient_name, patient_scan)
                                                # fullImageSizeInputDir = os.path.join(fullImageSizeDir, transformType,
                                                #                                      out, patient_name, patient_scan)

                                                fullImageSizeInputDir = os.path.join(fullImageSizeDir, transformType,
                                                                                     'FASGD_00_Iteration500_Timing_ConditionNumber4', patient_name, patient_scan)
                                            if transformType == 'Affine':
                                                t0 = ''
                                            else:
                                                t0 = os.path.join(resultDir, metricName, 'Affine',
                                                                  'FASGD_00_Iteration500_Timing_ConditionNumber4',
                                                                  patient_name, patient_scan, 'OriginalImage',
                                                                  'TransformParameters.0.txt')
                                            outputName = os.path.join(outDir, "OriginalImage")
                                            if not os.path.exists(outputName):
                                                os.makedirs(outputName)

                                            if t0 == '':
                                                cmdStr = "%s -f %s -m %s -out %s -p %s -threads %s" % \
                                                         (elastix, fixedImage, movingImage, outputName, parameter,
                                                          threadsNum)
                                            else:
                                                cmdStr = "%s -f %s -m %s -out %s -p %s -t0 %s -threads %s" % \
                                                         (elastix, fixedImage, movingImage, outputName, parameter,
                                                          t0, threadsNum)
                                            qsubStr = 'echo \'' + cmdStr + '\' | qsub -q compute.q -N ' + out + patient_name + '\n'
                                            fout.write(qsubStr)

                                            Prostate_registration(metricName, fixedImage, movingImage, fixedSegmentation,
                                                                movingSegmentation,
                                                                fixedSegmentationVtk, movingSegmentationVtk, outDir,
                                                                organName,
                                                                parameter, t0, fullImageSizeInputDir, threadsNum)
endTime = time.clock()
print(endTime - startTime)
