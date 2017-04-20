import os
from os.path import dirname, join, realpath
import subprocess
import amr_utils


CORNELL_AMR_DIR = join(dirname(dirname(realpath(__file__))), "tools/cornell-amr")
CAMR_DIR = join(dirname(dirname(realpath(__file__))), "tools/camr")


def prepare_input_file(filedir, sentences):
    assert filedir in [CORNELL_AMR_DIR, CAMR_DIR]
    input_filepath = "{0}/sentences.txt".format(filedir)
    os.system("rm {0}{1}".format(input_filepath, "*"))
    with open(input_filepath, 'w') as f:
        content = u'\n'.join(sentences)
        f.write(content.encode("UTF-8"))
    return input_filepath

def cornell_amr_parse(sentences, debug=False):
    if debug:
        stdout = None
        stderr = None
        log_level = "DEBUG"
    else:
        stdout = open(os.devnull, 'w')
        stderr = subprocess.STDOUT
        log_level = "ERROR"
    input_filepath = prepare_input_file(CORNELL_AMR_DIR, sentences)
    args = [
        "java",
        "-Xmx8g",
        "-jar",
        "{0}/dist/amr-1.0.jar".format(CORNELL_AMR_DIR),
        "parse",
        "rootDir={0}".format(CORNELL_AMR_DIR),
        "modelFile={0}/amr.sp".format(CORNELL_AMR_DIR),
        "sentences={0}".format(input_filepath),
        "logLevel={0}".format(log_level)
    ]
    process = subprocess.Popen(args, cwd=CORNELL_AMR_DIR, stdout=stdout, stderr=stderr)
    process.wait()
    assert process.returncode == 0, "Cornell AMR execution failed."
    output_filepath = "{0}/experiments/parse/logs/parse.out".format(CORNELL_AMR_DIR)
    output = amr_utils.read_from_file(output_filepath)
    return output

def camr_parse(sentences, debug=False):
    if debug:
        stdout = None
        stderr = None
    else:
        stdout = open(os.devnull, 'w')
        stderr = subprocess.STDOUT
    input_filepath = prepare_input_file(CAMR_DIR, sentences)
    args = [
        "python",
        "{0}/amr_parsing.py".format(CAMR_DIR),
        "-m",
        "preprocess",
        input_filepath
    ]
    process = subprocess.Popen(args, cwd=CAMR_DIR, stdout=stdout, stderr=stderr)
    process.wait()
    assert process.returncode == 0, "CAMR preprocessing failed."
    args = [
        "python",
        "{0}/amr_parsing.py".format(CAMR_DIR),
        "-m",
        "parse",
        "--model",
        "{0}/amr-anno-1.0.train.basic-abt-brown-verb.m".format(CAMR_DIR),
        input_filepath
    ]
    process = subprocess.Popen(args, cwd=CAMR_DIR, stdout=stdout, stderr=stderr)
    process.wait()
    assert process.returncode == 0, "CAMR parsing failed."
    output_filepath = "{0}.{1}".format(input_filepath, "all.basic-abt-brown-verb.parsed")
    output = amr_utils.read_from_file(output_filepath)
    return output

def parse_amr(sentences, parser="camr", debug=False):
	if parser == "cornell-amr":
		return cornell_amr_parse(sentences, debug=debug)
	if parser == "camr":
		return camr_parse(sentences, debug=debug)
	raise Exception("Unknown parser: {0}".format(parser))

if __name__ == "__main__":
    sentences = ["Every man loves a woman.", "Every man has a cat."]
    print('\n'.join(parse_amr(sentences, parser="camr", debug=True)))

