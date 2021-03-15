import os
import sys
import math
import argparse
import numpy as np
import pandas as pd
from scipy.stats import entropy
from PIL import Image


def calculate_entropy(path_to_file):
    ##### Get source bytes
    try:
        with open(path_to_file) as source:
            source_string = source.read()
            source_bytes = bytes(source_string, 'utf-8')
            byte_array = np.frombuffer(source_bytes, dtype=np.uint8)
    ##### Handle except if image is received.
    except UnicodeDecodeError:
        image_array = np.array(Image.open(path_to_file))
        byte_array = image_array.flatten()

    ##### Count values
    source_series = pd.Series(byte_array)
    counts = source_series.value_counts()

    ##### Compute entropy
    source_entropy = entropy(counts, base=2)

    return source_entropy    



if __name__ == "__main__":
    ##### Receives file to be compressed from command line.
    parser = argparse.ArgumentParser(description="Receives file to be encoded, the binary path and the decoded file path.")
    
    parser.add_argument('--file_to_compress', required=True, help='Path to file to be compressed.')
    parser.add_argument('--binary_file_path', required=False, help="Path to save binary file. "
                                                                   "If folders do not exist, they'll be created.")
    parser.add_argument('--decoded_file_path', required=False, help="Path to save decoded file. "
                                                                    "If folders do not exist, they'll be created.")
    parser.add_argument('--python_path', required=False, help="Path for python version of interest.", default="python3")

    ##### Read command line
    args = parser.parse_args(sys.argv[1:])

    ##### Showing file being decoder
    file_name = os.path.basename(args.file_to_compress)
    print(f"\n########## Encoding {file_name} file.")

    ##### Compute Source Entropy
    source_entropy = calculate_entropy(args.file_to_compress)
    print(f"\n##### The source entropy is {source_entropy:.5f} bits per symbol.")

    ##### Run Encoding command.
    print("\n##### Initializing Encoder")
    encoding_arguments = f"--file_to_compress {args.file_to_compress}"
    encoding_arguments += f" --binary_file_path {args.binary_file_path}" if (args.binary_file_path is not None) else ''
    os.system(f"{args.python_path} encoder.py {encoding_arguments}")

    ##### Run Decoding Command.
    print("\n##### Initializing Decoder")
    if args.binary_file_path is None:
        file_name = os.path.splitext(file_name)[0]
        args.binary_file_path = os.path.join("binary_files", file_name + '.bin')
    decoding_arguments = f"--binary_file {args.binary_file_path}"
    decoding_arguments += f" --decoded_file_path {args.decoded_file_path}" if (args.decoded_file_path is not None) else ''
    os.system(f"{args.python_path} decoder.py {decoding_arguments}")

    print("\n########## Finished!\n\n")