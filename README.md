# Project 1 - Huffman Coding

### Author:
- Name: Matheus Costa de Oliveira
- Registration: 17/0019039

### Course Information.
- Subject: Fundamentals of Signal Compression
- Department of Electrical Engineering
- University of Brasilia
___
## Install Required Packages.
The demanded packages can be installed with *pip* command by running the following command line.

```bash
python -m pip install -r requirements.txt
```
___
## Adaptative Huffman Coding

The AdaptativeBinaryTree class is implemented in the [adaptativebinarytree](adaptativebinarytree.py) file.

### Encode File 
To encode a file, the following command line should be excecuted.

```bash
<python_version> encoder.py --file_to_compress <path_to_file> --binary_file_path <path_for_saving_binary_file>
```

- *<python_version>* refers to your local python 3 version, inside the chosen environment.
- The argument *--binary_file_path* is not mandatory. If not provided, a new directory called *binary_files* will be created and a file *<original_file_name>.bin* will be saved.

### Decode File 
The command line for decoding a binary file is analogous to the one used in the encoding process.

```bash
<python_version> decoder.py --binary_file <path_to_binary> --decoded_file_path <path_for_saving_decoded_file>
```

- As with the command for encoding, only the argument *--binary_file* is required.
- If *--decoded_file_path* is not provided, the decoded file is saved in the path: *decoded_files/<original_file_name>*.

### Encode, Decode and Compute Entropy
In order to encode, decode and compare the rate obtained by the Adaptive Huffman Code with the first-order Entropy, the scripy [measure_adaptative_huffman_coding](measure_adaptative_huffman_coding.py) can be used. The command line is illustrated below.

```bash
<python_version> measure_adaptative_huffman_coding.py --file_to_compress <path_to_file> --binary_file_path <path_to_binary> --decoded_file_path <path_for_saving_decoded_file> --python_path <python_version_of_interest>
```

- Only the *--file_to_compress* argument is mandatory.
- Since the *measure_adaptative_huffman_coding* script execute both the encoder and decoder from command line, if some virtual environment or any not default python version is used, the relative path should be passed by the *--python_path* argument.