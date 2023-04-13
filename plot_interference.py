import argparse
import lhe2root_methods
import mplhep as hep
import matplotlib.pyplot as plt
import useful_funcs_and_constants


def ran(s):
    """A function to define the range format for this program

    Arguments:
        s -- The range in question

    Raises:
        argparse.ArgumentTypeError: Raises an error if formatted incorrectly

    Returns:
        two floats for the range bounds
    """
    try:
        left, right = map(float, s.split(','))
        return (left, right)
    except:
        raise argparse.ArgumentTypeError("Ranges must be of form 'left, right'!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', '--filenames',nargs=3, action="append", required=True,
                        help="The file you want to plot. Order them as <Interference file> <signal1> <signal2>")

    parser.add_argument('-l', '--labels', nargs=2, type=str, required=True,
                        help="The names of both your signals")

    parser.add_argument('-csf', '--crossSectionFile', default="CrossSections.csv",
                        help="The name of the file containing the cross sections for your data")

    parser.add_argument('-v','--value', default='M4L', choices=list(useful_funcs_and_constants.beautified_title.keys()),
                        help="The attributes you want to plot.")

    parser.add_argument('-r','--range', default=(6,9), type=ran,
                        help='The ranges for your attributes. Enclose your ranges with quotes and a leading space i.e. " -3.14,3.14"')

    parser.add_argument('-n', '--nbins', type=int, default=100,
                        help="The number of bins")

    parser.add_argument('-no', '--norm', action="store_true",
                        help="Option to normalize the area of the histogram to 1")

    parser.add_argument('-t', '--titles', default=[""], nargs="+",
                        help="Optional Figure Title")

    args = parser.parse_args()
    
    interf_plots = {}
    
    CrossSections = {}
    with open(args.crossSectionFile, newline='') as cs_file:
        for line in cs_file:
            line = line.strip().split(',')
            try:
                CrossSections[line[0]] = float(line[1]) #gets the cross section
            except:
                continue #skips any possible headers in the .csv file
    
    print(CrossSections)
    for (interefence_triplet, title) in zip(args.filenames, args.titles):
        interf_plots[title] = lhe2root_methods.plot_interference(*interefence_triplet, *args.labels, args.value, CrossSections,
                                                                nbins=args.nbins, title=title)
    
    for sample in interf_plots:
        scaled = lhe2root_methods.scale(interf_plots[sample][0], 1) if args.norm else interf_plots[sample][0]
        hep.histplot(scaled, interf_plots[sample][1], label=sample)
    
    plt.legend()
    plt.xlabel(useful_funcs_and_constants.beautified_title[args.value])
    plt.tight_layout()
    plt.savefig('question.png')
    # plt.show()