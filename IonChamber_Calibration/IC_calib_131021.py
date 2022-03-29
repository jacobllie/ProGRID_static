from dose_calibration import low_dose_estimation, high_dose_estimation, sec_to_min_and_sec
import numpy as np
import matplotlib.pyplot as plt


T = np.array([5,10,15,20]) #seconds
N_k = 43.77e-3 #Gy/nC
k_u = 1
mu_over_rho = 1.075
P_u = 1.02
k_TP = 1.021463
C = N_k * k_u * mu_over_rho * P_u * k_TP


"""
D has shape (4,4,4), 4 positions, 4 measurements for 5, 10, 15 and 20 seconds repeated 4 times.
"""
D = np.array([[[0.47,1.56,2.62,3.47] , [0.52,1.52,2.39,3.56] , [0.44,1.44,2.55,3.6], [0.5,1.41,2.48,3.55]] \
            ,[[0.37,1.37,2.45,3.52] , [0.38,1.36,2.35,3.49] , [0.41,1.51,2.48,3.54] , [0.4,1.42,2.4,3.53]] \
            ,[[0.55,1.54,2.43,3.6] , [0.4,1.48,2.54,3.55] , [0.39,1.48,2.56,3.62] , [0.36,1.44,2.55,3.51]] \
            ,[[0.44,1.57,2.48,3.53],[0.38,1.35,2.48,3.55],[0.45,1.41,2.56,3.53] , [0.35,1.39,2.54,3.6]]]) * C



pos_labels = ["A","B","C","D"]

#low dose estimation

low_dose = np.array([0.1,0.2,0.5])
_,mean_time = low_dose_estimation(T,D,low_dose,pos_labels)

print(mean_time)
plt.show()

for i in range(len(low_dose)):
    print("For {:.1f} Gy {:d} s".format(low_dose[i],int(mean_time[i])))


#high dose estimation

high_dose = np.array([1,2,5,10])
doserate = np.array([[11.75,11.69,11.79,11.82],[11.74,11.7,11.62,11.73],[12.1,11.98,12.03,12.02],\
[12,11.96,12.03,11.99]]) * C/60 #dose/s

_,mean_time = high_dose_estimation(high_dose,doserate)

print(mean_time)

for i, dose in enumerate(high_dose):
    print("For {:.1f} Gy".format(dose),end = " ")
    sec_to_min_and_sec(mean_time[i])
