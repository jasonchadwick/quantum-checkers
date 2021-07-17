import numpy as np

CNOT = np.array([[1,0,0,0],
                 [0,1,0,0],
                 [0,0,0,1],
                 [0,0,1,0]])

X = np.array([[0, 1],
              [1, 0]])

h = 1/np.sqrt(2)

H = np.array([[h,  h],
              [h, -h]])
