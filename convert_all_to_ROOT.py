import os
import argparse
import useful_funcs_and_constants
import lhe2root_methods

exceptions = { #There is no reason to store LHE files in the pycache folder. Use this to hardcode other exceptions in
    '__pycache__',
}
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('argument', type=str,
                        choices=useful_funcs_and_constants.lhe_2_root_options,
                        help="The argument to be passed to LHE2ROOT.py")
    
    parser.add_argument('-ea','--extra', type=str, nargs='+', default=[],
                        choices=useful_funcs_and_constants.lhe_2_root_args,
                        help="These are the extra arguments that can be passed to lhe2root")

    parser.add_argument('-c',"--clean", action='store_true',
                        help="removes all previously produced ROOT files and re-creates them in the specified directory")

    parser.add_argument('-cd', '--currentDirectory', type=str, default=os.getcwd(),
                        help="The directory you would like to recurse down from")

    parser.add_argument('-o', '--output', type=str, default='./',
                        help="The directory you would like to output both ROOT files and cross sections to. Set to 0 if you want the output to equal the input")

    parser.add_argument('-e','--exceptions', nargs='*',
                        help="Any folder exceptions you want to make to conversion. Useful if you have different argument types for LHE files",
                        default=[])

    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Option to make the process verbose")

    parser.add_argument('-w', '--write', default="CrossSections.csv",
                        help='Option to write out cross sections to the file named here. Enter "" if you do not want a file written.')

    parser.add_argument('-cut', '--cutDown', type=int, default=-1,
                        help="A number of events that you want to cut the lhe file down to the number of events you set")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.currentDirectory):
        raise argparse.ArgumentError("The directory of choice either does not exist, or is not a directory!")
    
    if not os.path.isdir(args.output):
        raise argparse.ArgumentError("The chosen output directory either does not exist, or is not a directory!")
    
    current_directory = args.currentDirectory
    exceptions = set(args.exceptions).union(exceptions)
    
    env = dict(os.environ)
    
    if not useful_funcs_and_constants.check_for_MELA(env):
        print("Current OS Environment:")
        [print(i,":",j,"\n") for i,j in env.items()]
        raise FileNotFoundError("MELA path not found!")
    
    if args.output == '0':
        args.output = current_directory
    
    file_cross_sections = lhe2root_methods.recursively_convert(current_directory=current_directory, output_directory=args.output, 
                                                                argument=args.argument, verbose=args.verbose, 
                                                                exceptions=exceptions, write=args.write, clean=args.clean,
                                                                cut_down_to=args.cutDown, env=env, other_args=args.extra)