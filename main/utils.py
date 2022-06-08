import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import pandas as pd
from scipy.optimize import curve_fit
from patsy import dmatrices
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
import cv2
from itertools import repeat
from scipy import stats
from scipy.optimize import minimize
from scipy.stats import t,chi2
from datetime import date


def K_means(dose, n_clusters,x,y):
    kmeans = KMeans(n_clusters = n_clusters)
    df = pd.DataFrame({"dose{}Gy".format(dose):np.ravel(x),"SF_{}Gy".format(dose):np.ravel(y)})
    fit = kmeans.fit(df)
    df["Clusters"] = fit.labels_
    if dose == 2:
        idx_1 = np.argwhere(np.logical_and(0.33 < x, x < 0.41))
        idx_2 = np.argwhere(np.logical_and(0.52 < x, x < 0.70))
        idx_3 = np.argwhere(np.logical_and(0.8 < x, x < 1.20))
        idx_4 = np.argwhere(np.logical_and(1.5 < x, x < 1.8))


        cluster_center1 = [np.mean(x[idx_1[:,0]]),np.mean(y[idx_1[:,0]])]
        cluster_center2 = [np.mean(x[idx_2[:,0]]),np.mean(y[idx_2[:,0]])]
        cluster_center3 = [np.mean(x[idx_3[:,0]]),np.mean(y[idx_3[:,0]])]
        cluster_center4 = [np.mean(x[idx_4[:,0]]),np.mean(y[idx_4[:,0]])]
        print(cluster_center1, cluster_center2)
        return df, cluster_center1, cluster_center2, cluster_center3, cluster_center4

    else:
        return df, fit.cluster_centers_[:,0],fit.cluster_centers_[:,1]

def mean_dose(lower_lim, upper_lim, doses):
    """
    Assumes doses with shape (m,n)
    """
    idx = np.argwhere(np.logical_and(lower_lim < doses, doses < upper_lim))
    mean = 0
    std = 0
    for i in range(doses.shape[0]):
        idx_tmp = idx[np.argwhere(idx[:,0] == 0)[:,0]]
        mean += np.mean(doses[i,idx_tmp[:,1]])
        std += np.std(doses[i,idx_tmp[:,1]])
    mean /= doses.shape[0]
    std /= doses.shape[0]
    return mean, std

def chi_squared(predicted, observed, num_datapoints, num_regressors):
    X = np.sum(((observed-predicted)/np.sqrt(predicted))**2)
    df = num_datapoints - num_regressors
    p_value = 1 - stats.chi2.cdf(X, df)
    return X, p_value

def deviance(predicted, observed):
    2*np.sum(observed * np.log(observed/predicted) - (observed - predicted))
    pass

def logLQ(d,alpha, beta):
    return -(alpha*d + beta*d**2)

def fit(model, x, y):
    popt, pcov = curve_fit(model, x, y)
    return popt

def design_matrix(regressors):#(len_respond_variables, x1, num_regressors, x2 = None, x3 = None, x4 = None):

    """if num_regressors == 1:
        X = np.zeros((len_respond_variables, num_regressors + 1))
        X[:,0] = 1
        X[:,1] = x1
    else:
        X = np.zeros((len_respond_variables, num_regressors + 1))
        X[:,0] = 1
        X[:,1] = x1
        X[:,2] = x1**2
        if num_regressors == 3:
            X[:,3] = x2
        if num_regressors == 4:
            X[:,3] = x2
            X[:,4] = x3
        if num_regressors == 5:
            X[:,5] = x4"""


def mean_survival(X, SC, rounding):
    dose_categories = np.unique(np.round(np.unique(X[:,1]),rounding))
    mean_SC = []
    SC_std = []
    if len(dose_categories)  < 2:
        mean_SC.append(np.mean(SC))
        SC_std.append(np.std(SC)/np.sqrt(len(SC)))
    else:
        for i in range(0,len(dose_categories)-1):

            idx = np.argwhere(np.logical_and(dose_categories[i] <= X[:,1], X[:,1] < dose_categories[i+1]))
            #plt.plot(dose_categories[i], 20-count,"*")
            if len(idx) != 0:
                 #print(dose_categories[i], dose_categories[i+1])
                 mean_SC.append(np.mean(SC[idx[:,0]]))
                 SC_std.append(np.std(SC[idx[:,0]])/np.sqrt(len(SC[idx[:,0]])))
    return np.array(mean_SC),np.array(SC_std), dose_categories

def poisson_regression(respond_variables, X , num_regressors, plot_title, save_path, legend, SC_lengths, kernel_size, save_results = False):
    #making design matrix. The intercept is 1
    #the survival to ctrl
    """
    This function takes dose and survival data, and uses Poisson regression to estimate
    average survival for given dose.
    We need to make a design matrix with the different parameters which are
    dose dose^2 and the g factor (area fraction)
    Design matrix looks like this

    [1,x00,x01,x02,x03
     1,x10,x11,x12,x13
     ...
     ...
     1,xn0,xn1,xn2,xn3]
    """
    #we interpolate the first parameter to fit a line to the poisson regression model
    #X[:,1] is doses

    colors = ["b","g","r","grey","m","y","black","saddlebrown"]

    #X_train, X_test, y_train, y_test = train_test_split(X, respond_variables,train_size = 0.8)
    # poisson_training_results = sm.GLM(respond_variables, X, family=sm.families.Poisson()).fit()
    model = sm.GLM(respond_variables, X, family=sm.families.Poisson())
    poisson_training_results = model.fit(full_output = True)

    pvalue = 1-chi2.cdf(poisson_training_results.pearson_chi2, X.shape[0] - num_regressors - 1)


    print("AIC for {} regressors".format(num_regressors))
    print(poisson_training_results.aic)





    if save_results == True:
        # f = open("C:\\Users\\jacob\\OneDrive\\Documents\\Skole\\Master\\data\\Survival Analysis Data\\2D analysis\\Poisson\\regression results\\GLM_results_OPEN&STRIPES&DOTS.txt", "a")
        f = open("C:\\Users\\jacob\\OneDrive\\Documents\\Skole\\Master\\data\\Survival Analysis Data\\2D analysis\\Poisson\\regression results\\GLM_results_test.txt", "a")

        f.write("\nnum regressors\t\t\tkernel size\t\t\tdate\t\t\tAIC\t\t\tGOF p-value\t# datapoints")
        f.write("\n{}\t\t\t\t{}\t\t\t\t{}\t\t{:.5f}\t\t{:.3f}\t\t{}".format(num_regressors,  kernel_size, date.today(), poisson_training_results.aic, pvalue, len(respond_variables)))
        f.close()

    summary = poisson_training_results.summary()
    summary2 = summary.as_csv()

    print(summary2)

    fitting_params = poisson_training_results.params
    if num_regressors == 5:
        fit_label = r"Fit: $ {:.3f} {:+.3f}D {:+.3f} D^2 {:+.3f} g {:+.3f} (1-g) {:+.3f} l$".format(fitting_params[0], fitting_params[1],fitting_params[2], fitting_params[3],  fitting_params[4], fitting_params[5])
    elif num_regressors == 4:
        fit_label = r"Fit: $ {:.3f} {:+.3f}D {:+.3f} D^2 {:+.3f} g {:+.3f} (1-g)$".format(fitting_params[0], fitting_params[1],fitting_params[2], fitting_params[3],  fitting_params[4])
    elif num_regressors == 3:
        fit_label = r"Fit: $ {:.3f} {:+.3f}D {:+.3f} D^2 {:+.3f} l$".format(fitting_params[0], fitting_params[1],fitting_params[2], fitting_params[3])
    elif num_regressors == 2:
        fit_label = r"Fit: $ {:+.3f} {:+.3f}D {:+.3f} D^2$".format(fitting_params[0], fitting_params[1],fitting_params[2])

    if save_results == True:
        beginningtex = """\\documentclass{report}
        \\usepackage{booktabs}
        \\begin{document}"""
        endtex = "\end{document}"

        f = open(save_path, 'w')
        f.write(beginningtex)
        f.write(poisson_training_results.summary().as_latex())
        f.write(endtex)
        f.close()
        #df.to_csv("C:\\Users\\jacob\\OneDrive\\Documents\\Skole\\Master\\data\\Survival Analysis Data\\GLM_results_39mm_OPEN.csv")
    #run test data through the model.
    poisson_predictions = poisson_training_results.get_prediction(X)

    #summary_frame() returns a pandas DataFrame
    predictions_summary_frame = poisson_predictions.summary_frame()



    """
    plot true vs predicted
    """
    predicted_counts = predictions_summary_frame['mean']

    mean_predicted_SC = mean_survival(X, predicted_counts, 1)
    print("predicted mean survival")
    #print(predicted_SC)
    #we sort the doses to get correct axis
    #dose_axis, correct_counts = zip(*sorted(zip(X_test[:,0], y_test)))
    #_,predicted_counts = zip(*sorted(zip(X_test[:,0], predicted_counts)))

    print(len(respond_variables))

    print(np.sum(SC_lengths))

    dose_axis = X[:,1]


    """2D plotting"""
    fig,ax = plt.subplots(figsize = (10,8))
    ax.set_title(plot_title)
    ax.set_xlabel("Dose [Gy]")
    ax.set_ylabel("SC")


    # ax.plot(X[SC_lengths[3]:SC_lengths[4] - 1,3], respond_variables[SC_lengths[3]:SC_lengths[4] - 1], 'o', label='Observed', color = colors[0], markersize = 3)
    # ax.plot(X[SC_lengths[3]:SC_lengths[4] - 1,3], predicted_counts[SC_lengths[3]:SC_lengths[4] - 1], "^", label = "Predicted", color = colors[0], markersize = 4)
    # ax.legend()
    # plt.show()
    for i in range(len(SC_lengths)-1):
        print(SC_lengths[i], SC_lengths[i+1])
        ax.plot(dose_axis[SC_lengths[i]:SC_lengths[i+1] - 1], respond_variables[SC_lengths[i]:SC_lengths[i+1] - 1], 'o', label='Observed' + legend[i], color = colors[i], markersize = 3)
        ax.plot(dose_axis[SC_lengths[i]:SC_lengths[i+1] - 1], predicted_counts[SC_lengths[i]:SC_lengths[i+1] - 1], "^", label = "Predicted" + legend[i], color = colors[i], markersize = 4)
    ax.legend(fontsize = 14, markerscale = 2)

    """
    3D plotting
    """

    # from mpl_toolkits import mplot3d
    # fig = plt.figure()
    # ax = plt.axes(projection='3d')
    #Z = respond_variables[SC_lengths[3]:SC_lengths[4]-1]

    #ax.scatter3D(X[SC_lengths[3]:SC_lengths[4]-1,1], X[SC_lengths[3]:SC_lengths[4]-1,3], Z, c=Z, cmap='Greens');
    #plt.show()

    # dose_axis = X[:,1]
    # plt.plot(dose_axis, predicted_counts, "bo", label=fit_label)
    # plt.plot(dose_axis, respond_variables, 'ro', label='Correct survival')
    # plt.title(plot_title)
    # plt.xlabel("Dose [Gy]")
    # plt.ylabel("SC")
    # plt.legend()
    #plt.show()
    return poisson_training_results, mean_predicted_SC, summary2

def data_stacking_2(grid, *args):
    """
    We stack all survival data with dose except 0 Gy ctrl, this will be added manually
    if needed
    """
    if grid == False:
        survival_2, survival_5, dose2, dose5 = args
        SC = np.concatenate((np.ravel(survival_2),
                             np.ravel(survival_5)))
        doses = np.array([dose2,dose5])
    if grid == True:
        survival_2, survival_5, survival_10, dose2, dose5, dose10 = args
        SC = np.concatenate((np.ravel(survival_2),
                             np.ravel(survival_5), np.ravel(survival_10)))
        doses = np.array([dose2,dose5,dose10])
    tot_dose_axis = np.ravel(np.repeat(doses, survival_2.shape[0]*survival_2.shape[1], axis = 0))
    return SC, tot_dose_axis

def data_stacking(dose0, dose2, dose5, survival_ctrl, survival_2,survival_5, dose10 = None, survival_10 = None):
    if survival_10 is not None and dose10 is not None:
        SC = np.concatenate((np.ravel(survival_ctrl),np.ravel(survival_2),
                             np.ravel(survival_5), np.ravel(survival_10)))
        doses = np.array([dose0,dose2,dose5,dose10])
    if survival_10 is None and dose10 is None:
        SC = np.concatenate((np.ravel(survival_ctrl),np.ravel(survival_2),
                                 np.ravel(survival_5)))
        doses = np.array([dose0,dose2,dose5])

    """
    numpy repeat example:
    x = np.array([[1,2],[3,4]])
    if you repeat x once
    y = np.repeat(x,2), you'll get [[1,2],
                                    [1,2],
                                    [3,4],
                                    [3,4],
    Thats why we make the initial the doses array, repeat it and the unravel so it becomes
    [1,2,1,2,3,4,3,4]
    """
    tot_dose_axis = np.ravel(np.repeat(doses, survival_ctrl.shape[0]*survival_ctrl.shape[1], axis = 0))
    return SC,tot_dose_axis

def logLQ(params, d):
    return (params[0]*d + params[1]*d**2)
def LQres(params,d,y):
    return (params[0]*d + params[1]*d**2) - y

def D(params,netOD):
    return params[0]*netOD + params[1]*netOD**params[2]

def confidence_band(fit_obj, dfdp, n, x_interp,func):
    k = len(dfdp)
    df = n- k - 1 #degrees of freedom
    hessian_approx_inv = np.linalg.inv(fit.jac.T.dot(fit.jac)) #follows H^-1 approx J^TJ
    std_err_res = np.sqrt(np.sum(fit.fun**2)/df)**2
    param_cov_low = std_err_res * hessian_approx_inv
    cov_D = dfdp.T.dot(param_cov).dot(dfdp)
    y_interp = func(fit.x,x_interp)

def dose_profile1(pixel_height, dose_array):
    mean_dose = np.zeros((len(dose_array),pixel_height))
    std_dose = np.zeros((len(dose_array),pixel_height))
    #confidence = np.zeros((len(dose_array), pixel_height))
    for i in range(len(dose_array)):
        mean_dose[i] = [np.mean(dose) for dose in dose_array[i]]
        std_dose[i] = [np.std(dose) for dose in dose_array[i]]
        #confidence[i] = std_dose[i]/np.sqrt(len(dose_array[i]))*t.ppf(0.95,len(dose_array[i]))
        #print(dose_array.shape)

    return mean_dose, std_dose
def dose_profile2(pixel_height,dose_matrix):
    """
    Loops over the entire heigth of the image,
    finding mean dose in each pixel row
    """
    dose_array = np.zeros(len(pixel_height))
    print(len(dose_array))
    for i in range(len(pixel_height)):
        dose_array[i] = np.mean(dose_matrix[i])

    return dose_array

def dose_fit_error(OD, dOD,dparam,param):
    da,db,dn = np.sqrt(dparam)
    a,b,n = param

    print(da,db,dn,a,b,n)
    return np.sqrt(OD**2 * da**2 + (OD**n)**2 * db**2 + (a + b*n * OD**(n-1))**2 * dOD**2 + \
                  (b*np.log(OD)*OD**n)**2 * dn**2)
def corrfunc(x, y, **kws):
    r, _ = stats.pearsonr(x, y)
    ax = plt.gca()
    ax.annotate("r = {:.2f}".format(r),
                xy=(.1, .9), xycoords=ax.transAxes)

if __name__ == "__main__":
    import skimage.transform as tf
    grid_image = cv2.imread("C:\\Users\\jacob\\OneDrive\\Documents\\Skole\\Master\\data\\310821\\Measurements\\Grid_Stripes\\EBT3_Stripes_310821_Xray220kV_5Gy1_001.tif",-1)
    grid_image = grid_image[10:722,10:497]
    grid_image = 0.299*grid_image[:,:,0] + 0.587*grid_image[:,:,1] + 0.114*grid_image[:,:,2]
    grid_image = tf.rescale(grid_image,4)
    grid_image = grid_image[200:2250,300:1750]


    plt.imshow(grid_image)
    plt.show()
