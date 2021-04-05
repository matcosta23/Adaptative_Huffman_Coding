import os
import sys
import cv2
import time
import argparse
import numpy as np

from PIL import Image
from tqdm import tqdm
from pathlib import Path
from bitstream import BitStream

from adaptativebinarytree import AdaptativeBinaryTree


class HuffmanEncoder():

    def __init__(self, source_path=None, bitstream_path=None, symbols_amount=2**8):
        self.source_path = source_path
        self.bitstream_path = bitstream_path
        
        # NOTE: It will be adopted as standard to use bytes as symbols.
        self.adaptative_binary_tree = AdaptativeBinaryTree(symbols_amount)


    def encode_source(self):
        ##### Get info about the source
        self.__get_source_info_from_file()
        ##### Instantiate bitstream
        self.instantiate_bitstream()
        ##### Encode Header
        self.__encode_header()
        ##### Encode source with Adaptative Huffman Coding.
        self.encode_with_adaptative_hc()
        ##### Save binary file
        self.__save_binary_file()

    
    def read_sequence_array(self, sequence):
        self.byte_array = sequence

    
    def instantiate_bitstream(self):
        self.bitstream = BitStream()

    def get_binary_string(self):
        return self.bitstream.__str__()


    def show_average_rate(self):
        ##### Show entire bitstream length
        print(f"Bitstream length: {len(self.bitstream.__str__())} bits;")
        ##### Show entire bitstream without header
        print(f"Bitstream length without header: {len(self.bitstream.__str__()) - self.header_length} bits;")
        ##### Compute Average Rate
        bitstream_length = len(self.bitstream.__str__())
        symbols_encoded = len(self.byte_array)
        mean_rate = bitstream_length/symbols_encoded
        print(f"Average rate: {mean_rate:.5f} bits per symbol.")


    def encode_with_adaptative_hc(self, verbose=True):
        ##### Define Auxiliary Function.
        def convert_string_to_boolean_list(string):
            bool_list = list(map(lambda bit: bool(int(bit)), list(string)))
            return bool_list

        ##### Measure encoding time.
        encoding_start = time.time()

        ##### Encode first symbol
        self.adaptative_binary_tree.insert_symbol(self.byte_array[0])
        self.bitstream.write(self.byte_array[0], np.uint8)
        ##### Encode remaining bitstream.
        iterator = tqdm(self.byte_array[1:], desc="Encoding Progress") if verbose else self.byte_array[1:]
        for byte in iterator:
            ##### Get symbol codeword
            byte_codeword = self.adaptative_binary_tree.get_symbol_codeword(byte)
            ##### If symbol is new, codeword for NYT and symbol's byte should be sent.
            if byte_codeword is None:
                nyt_codeword = self.adaptative_binary_tree.get_codeword_for_nyt()
                self.bitstream.write(convert_string_to_boolean_list(nyt_codeword))
                self.bitstream.write(byte, np.uint8)
            ##### If symbol exists, send its codeword.
            else:
                self.bitstream.write(convert_string_to_boolean_list(byte_codeword))
            ##### After getting the codeword, update Tree.
            self.adaptative_binary_tree.insert_symbol(byte)

        encoding_finish = time.time()
        if verbose:
            self.__print_process_duration(encoding_start, encoding_finish, "Encoding Process")
        
    
    ########## Private Methods
    def __get_source_info_from_file(self):
        # NOTE: Two approaches will be adopted for reading images and text files.
        ##### Trying to read as text:
        try:
            with open(self.source_path) as source:
                source_string = source.read()
                source_bytes = bytes(source_string, source.encoding)
                self.byte_array = np.frombuffer(source_bytes, dtype=np.uint8)
                self.shape = None

        ##### Handle except if image is received.
        except UnicodeDecodeError:
            image_array = np.array(Image.open(self.source_path))
            self.shape = image_array.shape
            self.byte_array = image_array.flatten()


    def __encode_header(self):
        ##### Define Auxiliary Function.
        def get_bool_list(value):
            bit_list = list('{0:04b}'.format(value))
            bool_list = list(map(lambda bit: True if bit == '1' else False, bit_list))
            return bool_list

        # NOTE: A flag is required to indicate whether it is an image.
        image_file = True if self.shape else False
        self.bitstream.write(image_file)

        ##### Image header.
        if image_file:
            # NOTE: The next flag will indicate if the image has 1 or 3 channels.
            three_channel_image = True if (len(self.shape) == 3) and (self.shape[-1] == 3) else False
            self.bitstream.write(three_channel_image)

            # NOTE: If the source is an image, the decoder needs to know its format. 
            # Instead of sending the whole dimensions, it will send the difference between width and height.
            height, width = self.shape[:2]
            dimension_difference = width - height
            positive_difference = True if dimension_difference >= 0 else False
            self.bitstream.write(positive_difference)
            dimension_difference = np.abs(dimension_difference) 
            difference_digits = list(str(dimension_difference))
            
            # NOTE: The amount of digits and the digit will be written with 4 bits.
            self.bitstream.write(get_bool_list(len(difference_digits)))
            for digit in difference_digits:
                self.bitstream.write(get_bool_list(int(digit)))

        ##### Get header length
        self.header_length = len(self.bitstream.__str__())


    def __save_binary_file(self):
        with open(self.bitstream_path, "wb") as bin_file:
            binary_string = get_binary_string()
            bin_file.write(binary_string.encode())
            bin_file.close()


    def __print_process_duration(self, starting_time, ending_time, process_name):

        def check_plural(value, string):
            string += 's' if value > 1 else ''
            return string
        
        time_difference = int(ending_time - starting_time)
        seconds = time_difference % 60
        minutes = (time_difference // 60) % 60
        hours = (time_difference // 60) // 60
        
        hours_string = check_plural(hours, f'{hours} hour') + ', ' if hours else ''
        minutes_string = check_plural(minutes, f'{minutes} minute') + ', ' if minutes else ''
        seconds_string = 'and ' + check_plural(seconds, f'{seconds} second') if seconds else 'and 0 second'

        print(process_name + ' took ' + hours_string + minutes_string + seconds_string + '.')




if __name__ == "__main__":
    ##### Receives file to be compressed from command line.
    parser = argparse.ArgumentParser(description="Receives file to be encoded and binary filepath.")
    
    parser.add_argument('--file_to_compress', required=True, help='Path to file to be compressed.')
    parser.add_argument('--binary_file_path', required=False, help="Path to save binary file. "
                                                                   "If folders do not exist, they'll be created.")

    ##### Read command line
    args = parser.parse_args(sys.argv[1:])
    
    ##### Define directory path.
    if args.binary_file_path:
        directory = Path(os.path.dirname(args.binary_file_path))
    else:
        directory = Path("binary_files")
        file_name = os.path.splitext(os.path.basename(args.file_to_compress))[0]
        args.binary_file_path = os.path.join(directory, file_name + '.bin') 
    
    ##### Create directory.
    if not directory.exists():
        directory.mkdir(parents=True)
    
    ##### Encode source.
    encoder = HuffmanEncoder(args.file_to_compress, args.binary_file_path)
    encoder.encode_source()
    encoder.show_average_rate()