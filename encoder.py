import os
import sys
import cv2 
import argparse
import numpy as np

from PIL import Image
from pathlib import Path
from bitstream import BitStream

import adaptativebinarytree as abt


class HuffmanEncoder():

    def __init__(self, source_path, bitstream_path):
        self.source_path = source_path
        self.bitstream_path = bitstream_path
        
        # NOTE: It will be adopted as standard to use bytes as symbols.
        self.adaptative_binary_tree = abt.AdaptativeBinaryTree(2**8)


    def encode_source(self):
        ##### Get info about the source
        self.__get_source_info()
        ##### Instantiate bitstream
        self.bitstream = BitStream()
        ##### Encode Header
        self.__encode_header()
        ##### Encode source with Adaptative Huffman Coding.
        self.__encode_with_adaptative_hc()
        ##### Save binary file
        self.__save_binary_file()

    
    ########## Private Methods
    def __get_source_info(self):
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


    def __encode_with_adaptative_hc(self):
        ##### Define Auxiliary Function.
        def convert_string_to_boolean_list(string):
            bool_list = list(map(lambda bit: bool(int(bit)), list(string)))
            return bool_list

        ##### Encode first symbol
        self.adaptative_binary_tree.insert_symbol(self.byte_array[0])
        self.bitstream.write(self.byte_array[0], np.uint8)
        ##### Encode remaining bitstream.
        for byte in self.byte_array[1:]:
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


    def __save_binary_file(self):
        with open(self.bitstream_path, "wb") as bin_file:
            bin_file.write(self.bitstream.__str__().encode())
            bin_file.close()



if __name__ == "__main__":
    ##### Receives file to be compressed from command line.
    parser = argparse.ArgumentParser(description="Receives file to be encoder and binary filepath.")
    
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