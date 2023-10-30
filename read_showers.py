import uproot
import numpy as np
import sys
import matplotlib.pyplot as plt
import keras
import conex_read
import convolutional_network as cn
import tensorflow as tf
import os
import glob
import re
from pathlib import Path

# converts a list of zenith angles to a list of the same angle with different lengths
def expandZenithAngles(zenithAngles, newLength):
    
    zenithAnglesList = list([list([x]) for x in zenithAngles])
    extendedZenithList = []
    for i in range(len(Xcx)):
        newZenithList = []
        for j in range(len(Xcx[i])):
            newZenithList.append(float(zenithAnglesList[i][0]))    
        extendedZenithList.append(newZenithList)

    zenithAngles = extendedZenithList
    for i in range(len(zenithAngles)):
        zenithAngles[i] = np.array(zenithAngles[i]) 

    return zenithAngles

def expandXcxdEdX(Xcx, dEdX, maxLength):
    for i, array in enumerate(Xcx):
        while len(Xcx[i]) < maxLength:
            Xcx[i] = np.append(Xcx[i], 0)
            dEdX[i] = np.append(dEdX[i], 0)

    for i, array in enumerate(dEdX):
        maxHeight = max(dEdX[i])
        for j, value in enumerate(dEdX[i]):
            dEdX[i][j] /= maxHeight

    return Xcx, dEdX

def runModel(model, learning_rate, batch_size, epochs, validation_split):
    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath='./best_saved_network',
        monitor='val_loss',
        mode='min',
        save_best_only=True,
        verbose=1  
    )


    fit = model.fit(
        X_train,
        mass_train,
        batch_size=batch_size,
        epochs=epochs,
        verbose=2,
        callbacks=[model_checkpoint_callback],
        validation_split=validation_split,
        workers = 100,
        use_multiprocessing = True
    )

    return fit

def plotdEdX(Xcx, dEdX):
    for i in range(100):
        plt.scatter(Xcx[i], dEdX[i], s=0.5)
        plt.xlabel('X')
        plt.ylabel('dEdX')
        plt.title('Energy deposit per cm')

    plt.show()
    plt.savefig('Energy function plot', dpi = 1000)


# if len(sys.argv) > 1:
#     file = sys.argv[1]
# else:
#     print("Usage: conex_read.py <rootfile.root>")
#     exit()




XcxAll = []
dEdXAll = []
zenithAll = []
massAll = []
massSingleNumberAll = []
count = 0

# Specify the directory path
directory_path = '/Data/Simulations/Conex_Flat_lnA/data/'

# Get a list of all folders within the directory
folder_list = [str(item) for item in Path(directory_path).iterdir() if item.is_dir()]
for i in range(len(folder_list)):
    folder_list[i] += '/showers'

for folder_path in folder_list:
    # folder_path = "/Data/Simulations/Conex_Flat_lnA/data/Conex_170-205_Prod1/showers"
    fileNames = glob.glob(os.path.join(folder_path, '*.root'))
    # Read data for network
    for fileName in fileNames:
        print("Reading file " + fileName)
        pattern = r'_(\d+)\.root'
        match = re.search(pattern, fileName)
        if match:
            mass = match.group(1)
            print(f"Mass is: {mass}")
        else:
            print("No match found.")

        try:
            Xcx, dEdX, zenith = conex_read.readRoot(fileName)
        except Exception as e:
            print(f"An exception occured: {e}")
            continue
        # Format all inputs to the network
        # maxLength = max(len(arr) for arr in Xcx)
        maxLength = 700
        Xcx, dEdX = expandXcxdEdX(Xcx, dEdX, maxLength)
        zenith = expandZenithAngles(zenith, maxLength)
        masses = []
        for i in range(maxLength):
            masses.append(float(mass))
        

        Xcx = np.vstack(Xcx)
        dEdX = np.vstack(dEdX)
        zenith = np.vstack(zenith)

        for showerXcx in Xcx:
            XcxAll.append(showerXcx)
        for showerdEdX in dEdX:
            dEdXAll.append(showerdEdX)
        for showerZenith in zenith:
            zenithAll.append(showerZenith)
            massAll.append(masses)
            massSingleNumberAll.append(float(mass))

        print("Finished reading file " + fileName)


X = np.stack([XcxAll, dEdXAll, zenithAll, massAll], axis = -1)
np.savez("/Data/nwoo/Training_Data/showers.npz", showers=X)
