import os
import sys
import time
import argparse
import numpy as np

from pathlib import Path
from PIL import Image 
from bitstream import BitStream, ReadError

from adaptativebinarytree import AdaptativeBinaryTree


class HuffmanDecoder():

    def __init__(self, binary_path=None, decoded_file_path=None, symbols_amount=2**8):
        self.binary_path = binary_path
        self.decoded_file_path = decoded_file_path
        self.adaptative_binary_tree = AdaptativeBinaryTree(symbols_amount)

    
    def decode_binary(self):
        ##### Read bitstream from file.
        self.__read_binary_file()
        ##### Decode header
        self.__decode_header()
        ##### Decode remaining bitstream.
        self.decode_with_adaptative_hc()
        ##### Save decoded file
        self.__save_decoded_file()


    def read_bitstream(self, bitstream):
        if isinstance(bitstream, BitStream):
            self.bitstream = bitstream
        elif isinstance(bitstream, str):
            bool_list = list(map(lambda bit: bool(int(bit)), list(bitstream)))
            self.bitstream = BitStream()
            self.bitstream.write(bool_list)
        else:
            raise TypeError("The provided bitstream should already be a bitstream.BitStream instance or a string.")

        
    def decode_with_adaptative_hc(self):
        ##### Measure decoding time.
        decoding_start = time.time()

        ##### Create attribute to save decoded bytes.
        self.decoded_bytes = []
        ##### Read first symbol and insert in the tree.
        symbol = self.bitstream.read(np.uint8, 1)[0]
        self.adaptative_binary_tree.insert_symbol(symbol)
        self.decoded_bytes.append(symbol)
        ##### Search for valid codeword.
        # NOTE: Since now the codeword do not have a fixed-lenght, we must look for a leaf node.
        bitstream_finished = False
        while bitstream_finished is not True:
            try:
                codeword_bool_list = self.bitstream.read(bool, 1)
                codeword = self.__convert_bool_list_to_str(codeword_bool_list)
                ##### Increase the codeword bit by bit, until reaching a valid symbol.
                symbol = None
                while symbol is None:
                    symbol = self.adaptative_binary_tree.get_symbol_from_codeword(codeword)
                    if symbol is None:
                        codeword_bool_list += self.bitstream.read(bool, 1)
                        codeword = self.__convert_bool_list_to_str(codeword_bool_list)
                    else:
                        if symbol == 'NYT':
                            symbol = self.bitstream.read(np.uint8, 1)[0]
                ##### After finding the symbol, it can be added to the decoded_bytes_list.
                self.adaptative_binary_tree.insert_symbol(symbol)
                self.decoded_bytes.append(symbol)
            except ReadError:
                bitstream_finished = True

        decoding_finish = time.time()
        self.__print_process_duration(decoding_start, decoding_finish, "Decoding Time")


    def get_decoded_bytes(self):
        return self.decoded_bytes


    ########## Private Methods
    def __read_binary_file(self):
        with open(self.binary_path, "rb") as bin_file:
            str_bitstream = bin_file.read().decode()
            bool_list = list(map(lambda bit: bool(int(bit)), list(str_bitstream)))
            self.bitstream = BitStream()
            self.bitstream.write(bool_list)


    def __decode_header(self):
        ##### Verify if file is image or text.
        self.image_file = self.bitstream.read(bool, 1)[0]

        # TODO: Test image header decoding.
        if self.image_file:
            ##### Check if image has 1 or 3 channels.
            self.three_channel_image = self.bitstream.read(bool, 1)[0]
            ##### Check if difference is positive
            positive_difference = self.bitstream.read(bool, 1)[0]
            ##### Read digits amount in difference value.
            digits_amount_bool_list = self.bitstream.read(bool, 4)
            digits_amount = int(self.__convert_bool_list_to_str(digits_amount_bool_list), 2)
            #### Read difference
            diff_str = ''
            for digit in range(digits_amount):
                digit_bool_list = self.bitstream.read(bool, 4)
                str_digit = str(int(self.__convert_bool_list_to_str(digit_bool_list)))
                diff_str += str_digit
            self.difference = int(diff_str) if positive_difference else (-int(diff_str))


    def __save_decoded_file(self):
        if self.image_file:
            ##### Get amount of pixels in the image.
            pixels_array = np.array(self.decoded_bytes)
            pixels_amount = len(pixels_array)/3 if self.three_channel_image else len(pixels_array)
            ##### Get image dimensions
            second_degree_coeff = [1, np.abs(self.difference), -pixels_amount]
            height = int(np.around(np.roots(second_degree_coeff).max(), 0))
            width = height + self.difference
            ##### Reshape Image
            channels = 3 if self.three_channel_image else 1
            img = np.squeeze(pixels_array.reshape((height, width, channels)))
            ##### Include image extension
            if self.three_channel_image:
                self.decoded_file_path += '.png' 
                file_format = 'PNG'
            else:
                self.decoded_file_path += '.bmp'
                file_format = 'BMP' 
            ##### Save image
            image = Image.fromarray(img)
            image.save(self.decoded_file_path, format=file_format)
        else:
            ##### Convert bytes to string
            text_string = ''.join([chr(byte) for byte in self.decoded_bytes])
            ##### Include extension in file path and save file.
            self.decoded_file_path += '.txt'
            with open(self.decoded_file_path, "wb") as decoded_file:
                decoded_file.write(text_string.encode())
                decoded_file.close()


    def __print_process_duration(self, starting_time, ending_time, process_name):

        def check_plural(value, string):
            string += 's' if value > 1 else ''
            return string
        
        time_difference = int(ending_time - starting_time)
        seconds = time_difference % 60
        minutes = (time_difference // 60) % 60
        hours = (time_difference // 60) // 60
        
        hours_string = check_plural(hours, f'{hours} hour') + ', ' if hours else ''
        minutes_string = check_plural(minutes, f'{minutes} minute') + ' and ' if minutes else ''
        seconds_string = check_plural(seconds, f'{seconds} second') if seconds else '0 second'

        print(process_name + ' took ' + hours_string + minutes_string + seconds_string + '.')


    def __convert_bool_list_to_str(self, bool_list):
        bs = ''.join(['1' if bit == True else '0' for bit in bool_list])
        return bs



if __name__ == "__main__":
    ##### Receives binary to be decoded from command line.
    parser = argparse.ArgumentParser(description="Receives binary file and path to save reconstructed file.")
    
    parser.add_argument('--binary_file', required=True, help='Path to binary file.')
    parser.add_argument('--decoded_file_path', required=False, help="Path to save decoded file. "
                                                   "If folders do not exist, they'll be created.")

    ##### Read command line
    args = parser.parse_args(sys.argv[1:])
    
    ##### Define directory path.
    if args.decoded_file_path:
        directory = Path(os.path.dirname(args.decoded_file_path))
    else:
        directory = Path("decoded_files")
        file_name = os.path.splitext(os.path.basename(args.binary_file))[0]
        args.decoded_file_path = os.path.join(directory, file_name) 
    
    ##### Create directory.
    if not directory.exists():
        directory.mkdir(parents=True)
    
    ##### Decode binary.
    decoder = HuffmanDecoder(args.binary_file, args.decoded_file_path)
    decoder.decode_binary()