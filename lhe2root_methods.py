import os
import re
import uproot
import pandas as pd
import numpy as np
import mplhep as hep
import lhe_constants
import lhefile_methods
import matplotlib as mpl
import matplotlib.pyplot as plt

plt.style.use(hep.style.ROOT)
mpl.rcParams['axes.labelsize'] = 40
mpl.rcParams['xaxis.labellocation'] = 'center'

def scale(counts, scaleto):
    """This function scales histograms according to their absolute area under the curve (no negatives allowed!)

    Parameters
    ----------
    counts : list[Union[int,float]]
        A list of bin counts
    scaleto : float
        The absolute area to scale to

    Returns
    -------
    list[float]
        The scaled histogram
    """
    counts = counts.astype(float)
    signs = np.sign(counts) #makes sure to preserve sign
    counts = np.abs(counts)
    
    return signs*counts*scaleto/np.sum(counts)


def get_cross_section_from_LHE_file(LHE_file_path):
    """Gets the cross section and its uncertainty from a given LHE file using regular expressions

    Parameters
    ----------
    LHE_file_path : str
        The file path for the LHE file

    Returns
    -------
    Tuple[str, str]
        A tuple of strings containing the cross section and its uncertainty
    """
    
    cross_section = uncertainty = ""
    
    with open(LHE_file_path) as getting_cross_section:
        head = getting_cross_section.read()
        
        #This regex was made by the very very helpful https://pythex.org/ (shoutout professor Upsorn Praphamontripong)
        cross_finder = re.compile(r'<init>\n.+\n.+(\d+\.\d+E(\+|-)\d{2})\s+(\d+\.\d+E(\+|-)\d{2})\s+(\d+\.\d+E(\+|-)\d{2})(\d|\s)+</init>')
        cross_section_match = re.search(cross_finder,head)
        
        cross_section = cross_section_match.group(1)
        
        uncertainty = cross_section_match.group(3)
        
    return cross_section, uncertainty #returns the cross section and its uncertainty        

def check_for_MELA():
    """A function that checks whether or not you have the environment variables for MELA set up within your terminal

    Returns
    -------
    bool
        A boolean as to whether or not MELA is properly set up
    """
    if "LD_LIBRARY_PATH" not in os.environ: #this library path is set up by the MELA setup script
        print("MELA environment variables have not been set up correctly")
        if 'HexUtils' in os.getcwd():
            print("Run './install.sh' in the directory above HexUtils to set these up!")
        else:
            print("Run './setup.sh' in the MELA directory to set these up!")
            
        return False
    
    return True


def recursively_convert(current_directory, output_directory, argument, clean=False, verbose=False, exceptions=set(), write=""):
    """This function will recurse through every directory and subdirectory in the place you call it, 
    and attempt to convert those files to ROOT files using lhe2root

    Parameters
    ----------
    current_directory : str
        The directory to start recursing downwards from
    output_directory : str
        The directory to output results to
    argument : str
        the lhe2root argument to use (see lhe_2_root_options in lhe_constants)
    clean : bool, optional
        If True, this function will wipe any old conversion and re-convert the files, by default False
    verbose : bool, optional
        If true, the function will be verbose, by default False
    exceptions : set, optional
        Any absolute path with this string in it will be ignored, by default set()
        NOTE: This is the case for any string in the path! folders of path <exception>/<other folder> will be ignored
        The same goes for folders where a substring of the folder matches the name in the exception - useful for catching multiple folders!
        Name your folders carefully!
    write : str, optional
        If a string, this will be the file that you will write the cross sections to. The file will be comma-separated, by default ""

    Returns
    -------
    dict
        Returns a dictionary with the cross section/uncertainty pairs for every file

    Raises
    ------
    FileNotFoundError
        If the output directory is not found/not a directory raises an error
    """
    
    if output_directory[-1] != '/':
        output_directory += '/'
    
    if not os.path.isdir(output_directory):
        raise FileNotFoundError(output_directory + " is not a directory!")
    
    cross_sections = {}
    
    for candidate in os.listdir(current_directory):
        # print(candidate)
        candidate = os.fsdecode(candidate)
        
        candidate_filename = candidate[:candidate.rfind('.')]
                
        candidate = current_directory + '/' + candidate
        # print(candidate)
        
        is_exempt = False
        for exemption in exceptions:
            if exemption in candidate:
                is_exempt = True
        
        
        if (os.path.isdir(candidate)) and (not is_exempt): #convert all the LHE files in every directory below you
            one_folder_below = recursively_convert(candidate, argument, clean, verbose, exceptions)
            cross_sections.update(one_folder_below)
        
        if candidate.split('.')[-1] != 'lhe':
            if clean and candidate.split['.'][-1] == '.root':
                lhe_constants.print_msg_box("Removing " + candidate, title="Cleaning directory " + current_directory)
                os.remove(candidate)
                
            continue
        
        else:
            output_filename = 'LHE_' + candidate_filename + '.root'
            
            running_str = "python3 lhe2root.py --" + argument + " " + output_directory + output_filename + ' '
            running_str += candidate
            
            if not verbose:
                running_str += ' > /dev/null 2>&1'
            
            cross_section, uncertainty = get_cross_section_from_LHE_file(candidate) #these are currently strings!
            
            cross_sections[current_directory + '/' + output_filename] = (cross_section, uncertainty)
            
            titlestr = "Generating ROOT file for ./" + os.path.relpath(candidate)
            
            number_events = len(lhefile_methods.get_all_events(candidate))
            
            lhe_constants.print_msg_box("Input name: " + candidate.split('/')[-1] + #This is the big message box seen per LHE file found
                "\nOutput: " + str(os.path.relpath(output_directory + output_filename)) + 
                "\nArgument: " + argument + 
                "\n\u03C3: " + cross_section + " \u00b1 " + uncertainty + 
                "\nN: " + "{:e}".format(number_events) + " events",
                title=titlestr, width=len(titlestr))
            
            os.system(running_str)
    
    if write:
        with open(output_directory + write, "w+") as f:
            f.write("Filename, Cross Section, Uncertainty\n")
            for fname, (crosssection, uncertainty) in cross_sections.items():
                f.write(fname + ', ' + crosssection + ', ' + uncertainty + '\n')
                
    return cross_sections



def plot_one_quantity(filenames, attribute, xrange, nbins=100, labels=[], norm=False, title=""):
    """This function plots one quantity of your choice from ROOT files!

    Parameters
    ----------
    filenames : list[str]
        The ROOT files you are plotting from
    attribute : str
        The TBranch you are plotting (the files should have the same names for branches)
    xrange : tuple[float, float]
        The range for your x axis for this attribute
    nbins : int, optional
        The number of bins. This can either be a number or a list, by default 100
    labels : list, optional
        The labels for each file plotted, by default []
    norm : bool, optional
        Whether to normalize the plotting areas to 1 for easier comparison, by default False
    title : str, optional
        An extra "title" on the x label that is concatenated, by default ""

    Returns
    -------
    dict
        A dictionary of NumPy style histogram tuple of counts and bins with the filename as the key

    Raises
    ------
    ValueError
        If your list of labels and list of filenames are not the same length
    ValueError
        If you choose a column that is undefined
    """
    if labels and len(labels) != len(filenames):
        raise ValueError("labels and files should be the same length!")
    
    histograms = {}
    
    for n, file in enumerate(filenames):
        with uproot.open(file) as f:
            keys = f.keys()
            f = f[keys[0]].arrays(library='pd')
            
            try:
                value = f[attribute]
            except:
                raise ValueError("You can only choose from these attributes:\n" + str(list(f.columns)))
            
            hist_counts, hist_bins = np.histogram(value, range=xrange, bins=nbins)
            
            histograms[file] = (hist_counts, hist_bins)
            
            if norm:
                hist_counts = scale(hist_counts, 1)
                
            if labels:
                hep.histplot(hist_counts, hist_bins, lw=2, label=labels[n])
            else:
                hep.histplot(hist_counts, hist_bins, lw=2)
                
            plt.xlim(xrange)
            
            if attribute in lhe_constants.beautified_title:
                plt.xlabel(lhe_constants.beautified_title[attribute] + title, horizontalalignment='center', fontsize=30)
            else:
                plt.xlabel(attribute + title, horizontalalignment='center', fontsize=30)
                
    if labels:
        plt.legend()
        
    plt.tight_layout()
    plt.show()
    
    return histograms


def plot_interference(mixed_file, pure1, pure2, pure1Name, pure2Name, attribute, cross_sections, nbins=100, title=""):
    """Plots the interference between two samples given a file containing a mixture of the two, and two "pure" samples

    Parameters
    ----------
    mixed_file : str
        The ROOT file containing a simulation of pure1 and pure2 together
    pure1 : str
        ROOT file for one of the two items (no mixing)
    pure2 : str
        ROOT file for the other of the two items (no mixing)
    pure1Name : str
        The name for what this sample is called
    pure2Name : str
        The name for what this sample is called
    attribute : str
        The thing you are plotting (i.e. M4L, phi, etc.)
    cross_sections : dict
        A dictionary containing the cross sections of each file in the following format: {filename: cross section}
    nbins : int, optional
        The number of bins for your plot. This can either be an integer or a list of bins, by default 100
    title : str, optional
        An extra "title" on the x label that is concatenated, by default ""

    Returns
    -------
    _type_
        The interference portion between the three plots
    """
    
    mixed_file = os.path.abspath(mixed_file)
    pure1 = os.path.abspath(pure1)
    pure2 = os.path.abspath(pure2)
    
    interf_sample = BW1_sample = BW2_sample = pd.DataFrame()
    
    with uproot.open(mixed_file) as interf: #Opening all of these in the same statement might cause memory issues. So here we are!
        interf_sample = interf[interf.keys()[0]].arrays(library='pd')
        
    if attribute not in interf_sample.columns:
        return
        
    with uproot.open(pure1) as rawBW1:
        BW1_sample = rawBW1[rawBW1.keys()[0]].arrays(library='pd')
        
    with uproot.open(pure2) as rawBW2:
        BW2_sample = rawBW2[rawBW2.keys()[0]].arrays(library='pd')
        
    
    interf_hist, bins = np.histogram(interf_sample[attribute], range=lhe_constants.ranges[attribute], bins=nbins)
    BW1_hist, _ = np.histogram(BW1_sample[attribute], range=lhe_constants.ranges[attribute], bins=bins)
    BW2_hist, _ = np.histogram(BW2_sample[attribute], range=lhe_constants.ranges[attribute], bins=bins)
    
    # print('%E' % CrossSections[pure1][0], '%E' % CrossSections[pure2][0], '%E' % np.sqrt(CrossSections[pure1][0]*CrossSections[pure2][0])
    #     , '%E' % CrossSections[mixed_file][0])
    
    interf_hist = scale(interf_hist, cross_sections[mixed_file])
    BW1_hist = scale(BW1_hist, cross_sections[pure1])
    BW2_hist = scale(BW2_hist, cross_sections[pure2])
    
    interf_actual = interf_hist - BW1_hist - BW2_hist
    
    plt.figure()
    plt.gca().axhline(lw=3, linestyle='--', color='black', zorder=0)
    
    hep.histplot(BW1_hist, bins, label=pure1Name, lw=2)
    hep.histplot(BW2_hist, bins, label=pure2Name, lw=2)
    hep.histplot(interf_hist, bins, label=pure1Name + '/' + pure2Name, lw=2)
    # print(interf_hist)
    
    hep.histplot(interf_actual, bins, label=pure1Name + '/' + pure2Name + ' Interference', lw=2)
    
    plt.xlabel(lhe_constants.beautified_title[attribute] + " " + title, horizontalalignment='center', fontsize=20)
    plt.xlim(lhe_constants.ranges[attribute])
    plt.legend()
    plt.tight_layout()
    
    plt.show()
    
    return interf_actual, bins