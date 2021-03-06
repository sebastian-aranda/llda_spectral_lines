import sys
import csv
import math

import numpy as np

from operator import itemgetter
from bisect import bisect_left
from random import randint

spectral_file_out = "./spectrum_document.dat"

if (len(sys.argv) != 5):
	print("e.g. python synthetic2spectrum.py ../Synthetic_Spectrums_125/Carbon_Monoxide/Carbon_Monoxide__COv\=0__1-0/trainingData.csv 0 ./llda_train_input/hot_cores_tr_features.dat 0")
	sys.exit(1)

fileName = sys.argv[1]
channeling = int(sys.argv[2])
featuresFile = sys.argv[3]
choosen_line = int(sys.argv[4])

sigma_thresshold = 2.0

def takeClosest(myList, myNumber, thresshold = 200000):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    after_delta = after - myNumber
    before_delta = myNumber - before
    if after_delta < before_delta and after_delta < thresshold:
        return after
    elif before_delta < after_delta and before_delta < thresshold:
        return before
    else:
        return before

with open(featuresFile) as f:
    tokens = f.readline().split()
    vocabulary = [int(token) for token in tokens]

spectrum = list()
with open(fileName) as csvfile:
    #FORMAT: freq[GHz]:energy[K],
    spamreader = csv.reader(csvfile, delimiter=',')
    for i, row in enumerate(spamreader):
        if i != choosen_line:
            continue
        
        for token in row:
            pairs = token.split(':')
            frequency = float(pairs[0])/(10**4) #Transform to GHz
            #frequency_ch = int(math.floor(frequency*10**channeling)) #Frequency in GHz
            frequency_ch = int(round(frequency*10**channeling)) #Frequency in GHz
            energy = float(pairs[1])
            spectrum.append((frequency_ch, takeClosest(vocabulary,frequency_ch),energy))

spectrum.sort(key=itemgetter(0))
print("From: "+str(spectrum[0])+" To: "+str(spectrum[-1]))

#Calculating Mean & Standard Deviation
energy_array = np.array([e for f,fc,e in spectrum])
energy_mean = np.mean(energy_array)
energy_std = np.std(energy_array)
print("Max Frequency: "+str(spectrum[np.argmax(energy_array)][0]))
print("Mean: "+str(energy_mean))
print("Sigma: "+str(sigma_thresshold)+"x"+str(energy_std))

spectrum_document = list()
for freq_channeled, freq_casted, energy in spectrum:
	tf = int(math.ceil(np.log2(energy+1))) if energy > energy_std*sigma_thresshold else 0 #TF v2.2
	#spectrum_document.extend([str(freq_channeled) for i in range(tf)])
	spectrum_document.extend([str(freq_casted) for i in range(tf)])

#Saving file
mFile_out = open(spectral_file_out,'w')
print("Generated File:")
print(" ".join(spectrum_document)+"\n")
mFile_out.write(" ".join(spectrum_document)+"\n")
mFile_out.close()
