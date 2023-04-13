import tqdm
import argparse
import useful_funcs_and_constants
import lhe_reader


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('filenames',nargs='+',
                        help="The files you want to check")
    
    args = parser.parse_args()
    
    for file in tqdm.tqdm(args.filenames, total=len(args.filenames)):
        reader = lhe_reader.lhe_reader(file)
        N_events = reader.num_events
        useful_funcs_and_constants.print_msg_box("{:.2e}".format(N_events), title=file, width = len(file) + 3)