import os
import yaml
import json
import argparse

from preprocessed import execute

file_dct = {
    "TM.pdf": "tm",
    "tnb_physical.jpg": "tnb-full",
    "tnb_digital.jpg": "tnb-online",
}

with open("templates.yaml") as f:
        templates = yaml.load(f, Loader=yaml.FullLoader)

def check_file_existence(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

def main():
    debug = False
    filename = args.file_path

    try:
        check_file_existence(args.file_path)
        print(f"The file '{args.file_path}' exists.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)

    result = execute(filename, templates, file_dct, debug)
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File")
    parser.add_argument("file_path", type=str, help="Path to the file")
    args = parser.parse_args()

    main()
