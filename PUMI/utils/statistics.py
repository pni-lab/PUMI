def calc_friston_twenty_four(in_file):
    """

    Method to calculate friston twenty-four parameters

    Parameters:
        in_file (str): input movement parameters file from motion correction

    Returns:
        new_file (str): output 1D file containing 24 parameter values

    """

    import numpy as np
    import os

    data = np.genfromtxt(in_file)
    data_squared = data ** 2
    new_data = np.concatenate((data, data_squared), axis=1)
    data_roll = np.roll(data, 1, axis=0)
    data_roll[0] = 0
    new_data = np.concatenate((new_data, data_roll), axis=1)
    data_roll_squared = data_roll ** 2
    new_data = np.concatenate((new_data, data_roll_squared), axis=1)
    new_file = os.path.join(os.getcwd(), 'fristons_twenty_four.1D')
    np.savetxt(new_file, new_data, delimiter=' ')
    return new_file


def calculate_FD_Jenkinson(in_file):
    """

    Method to calculate friston twenty four parameters

    Parameters:
        in_file (str): input movement parameters file from motion correction

    Returns:
        new_file (str): path to output file

    """

    import numpy as np
    import os
    import math

    out_file = os.path.join(os.getcwd(), 'FD_J.1D')

    lines = open(in_file, 'r').readlines()
    rows = [[float(x) for x in line.split()] for line in lines]
    cols = np.array([list(col) for col in zip(*rows)])

    translations = np.transpose(np.diff(cols[3:6, :]))
    rotations = np.transpose(np.diff(cols[0:3, :]))

    flag = 0
    rmax = 80.0  # The default radius (as in FSL) of a sphere represents the brain

    out_lines = []

    for i in range(0, translations.shape[0] + 1):

        if flag == 0:
            flag = 1
            # first timepoint
            out_lines.append('0')
        else:
            r = rotations[i - 1,]
            t = translations[i - 1,]
            FD_J = math.sqrt((rmax * rmax / 5) * np.dot(r, r) + np.dot(t, t))
            out_lines.append('\n{0:.8f}'.format(FD_J))

    with open(out_file, "w") as f:
        for line in out_lines:
            f.write(line)
    return out_file


def mean_from_txt(in_file, axis=None, header=False, out_file='mean.txt'):
    """

    Calculate column-means, row-means or the global mean depending on the 'axis' parameter and save it to
    another text-file.

    Caution: Name in the old PUMI was txt2MeanTxt

    Parameters:
        in_file (str): input file
        axis (None/int/(int,int)): axis or axes along which the means are computed.
                                   Default: Compute mean of the flattened array.
        header (bool): Drop line if True
        out_file (str): Name of the resulting text-file. If only the filename is given, it will be saved into the
                        current working directory.

    Returns:
        new_file (str): path to new file

    """
    import numpy as np
    import os

    if header:
        print("drop first line")
        data = np.loadtxt(in_file, skiprows=1)
    else:
        print("don't drop first line")
        data = np.loadtxt(in_file)
    mean = data.mean(axis=axis)
    np.savetxt(out_file, [mean])
    if out_file.startswith('/'):
        new_file = out_file
    else:
        new_file = os.path.join(os.getcwd(), out_file)  # need to add '/' manually?
    return new_file


def max_from_txt(in_file, axis=None, header=False, out_file='max.txt'):
    """

    Saves the maximum along a given axis into another text-file.

    Caution: Name in the old PUMI was txt2MaxTxt

    Parameters:
        in_file (str): input file
        axis (None/int/(int,int)): axis or axes along the maximum values are computed.
                                   Default: Use flattened array.
        header (bool): Drop line if True
        out_file (str): Name of the resulting text-file. If only the filename is given, it will be saved into the
                        current working directory.

    Returns:
        new_file (str): path to new file

    """
    import numpy as np
    import os

    if header:
        print("drop first line")
        data = np.loadtxt(in_file, skiprows=1)
    else:
        print("don't drop first line")
        data = np.loadtxt(in_file)
    dmax = data.max(axis=axis)
    np.savetxt(out_file, [dmax])
    if out_file.startswith('/'):
        new_file = out_file
    else:
        new_file = os.path.join(os.getcwd(), out_file)  # need to add '/' manually?
    return new_file
