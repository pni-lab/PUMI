def get_repetition_time(in_file):
    """

    Get time-to-repetition of the scan.

    CAUTION: Name in the old PUMI is get_scan_info

    Parameters
    ----------
    in_file (str): Path to (functional!) nifti-image

    Returns
    -------
    TR (float): Time-to-repetition of file
    """

    import nibabel as nib
    func = nib.load(in_file)
    header = func.header
    repetition_time = header['pixdim'][4]
    return float(repetition_time)
