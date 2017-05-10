# Coding the tax code: Regulation to Formalism

Create AI techniques developed to translate law into software and that support intelligent reasoning and argumentation
around it. This project focuses on the regulatory form of law, e.g. tax law. It will involve developing an automatic 
parsing system for translating regulations into a formalism.

## Installation

Run the commands below install the requirements.
```bash
./download-irc.sh
./install-prover9.sh
./install-tools.sh
pip install -r requirements.txt
```

Install `nltk` tokenizer
```
python -c "import nltk;nltk.download(\"punkt\")"
```

The scripts:
- `download-irc.sh` will download Internal Revenue Code in XML and place it in the directory `irc/xml` with
 filename `irc.xml`. 
- `install-prover9.sh` will install install [Prover9 and Mace4](http://www.cs.unm.edu/~mccune/prover9/download/) in `/usr/local/bin/prover9`, which is necessary for theorem proving and model building. 
- `./install-tools.sh` will install semantic parsing tools ([CAMR](https://github.com/c-amr/camr) and [Cornell AMR](https://github.com/cornell-lic/amr)) in the directory `tools/`.

## Usage

There are multiple scripts that can be run in combination with `pipeline.py` or independently. To run:
- Crawl the IRC with `irc_crawler.py`. Run the command below, replacing `LEVEL_ID` with the level identifier desired. The level identifier specifies the level (section, subsection, paragraph, etc.) to find. It should have pattern `s[section]/[subsection]/[paragraph]/[subparagraph]/[clause]/[subclause]/[item]/[subitem]/[subsubitem]`. For example, `s163/h/1` specifies section 163, subsection h, paragraph 1.
```
python scripts/irc_crawler.py [--level-id LEVEL_ID]
```

- Extract definitions with `definition_extractor.py`. Run the command below, replacing `LEVEL_ID` with the level identifier desired.
```
python scripts/definition_extractor.py [--level-id LEVEL_ID]
```

- Extract rules with `rule_extractor.py`. Run the command below, replacing `LEVEL_ID` with the level identifier desired.
```
python scripts/rule_extractor.py [--level-id LEVEL_ID]
```

- Query and prove default logic with `default_logic.py`. Run `python scripts/default_logic.py`. This will run some default logic examples, displaying the background theory, default rules, as well as a goal and its result. The examples are from Sarah Lawsky. **Note** There are two threads running and the script might take a while to exit (an issue has been opened with `nltk`, but no reply yet...).

- Semantic parsing software:
  
  - `candc_boxer_api.py`, simply run `python scripts/candc_boxer_api.py`. This will run a semantic parsing example by making a call to C&C/Boxer and displaying the result in both Discourse Representation Structure (DRS) and First-Order Logic (FOL). **Note** The API is currently hosted on an MIT CSAIL openStack virtual machine.

  - `parse_amr.py`, simply run `python scripts/parse_amr.py`. This will run a semantic parsing example by making a call to [CAMR](https://github.com/c-amr/camr) and displaying the result in Abstract Meaning Representation (AMR).

- A pipeline for parsing IRC to a default logic formalism, with intermediate representations is done by `pipeline.py`. Run the command below. This will crawl the IRC for the specified level, parse the sentences at that level to the specified representation, and write the output to the specified file (default is `pipeline.out`).
```
python scripts/pipeline.py [--level-id LEVEL_ID]
                           [--representation {fol,amr,amr2fol,default_logic}]
                           [--output-file OUTPUT_FILE]
                           [--dl-hack]
```
Run the examples of default logic from Sarah Lawsky with `python scripts/pipeline.py --dl-hack --representation default_logic`

Input can fail on too long sentences (which there are a few of in the IRC). Back up parsers are called if C&C/Boxer fails. **Note** we cannot find the default rules yet, the `--dl-hack` uses hardcoded assumptions for Section 163.

The steps in `pipeline.py` are:
- Crawl the IRC with `irc_crawler.py`
- Extract definitions and rules
- Parse the requested sentences to a representation, e.g. 
  - `amr` (abstract meaning representation)
  - `fol` (First Order Logic)
  - `amr2fol` (AMR to FOL) 
  - `default_logic`, in the default logic representation
    - Definitions are extracted with `definition_extractor.py`
    - Default rules are searched for based on the representation
    - The default logic is formulated, the default rules are added in order of discovery, i.e. earlier rules have lower priority

## Stats scripts

We also provide some scripts to generate statistics and plots for extracted definitions and rules. These can be found in the `scripts/stats` directory. To run `scripts/stats/definition_stats.py` and `scripts/stats/rule_stats.py`:
```
python -m scripts.stats.definition_stats [--output-dir OUTPUT_DIR]
                                         [--plot]
                                         [--plot-sections]

python -m scripts.stats.rule_stats [--output-dir OUTPUT_DIR]
                                   [--plot]
                                   [--plot-sections]
```
After running these, you can also run `scripts/stats/semparsing_stats.py` to generate counts on C&C/Boxer crashes when running with definitions and rules as input.
```
python -m scripts.stats.semparsing_stats [--output-file OUTPUT_FILE]
                                         [--definitions-filepath DEF_FILEPATH]
                                         [--rules-filepath RULES_FILEPATH]
```
Finally, the outputs of these scripts can be used to plot histograms with the `scripts/stats/plot_hists.py` script.
```
python -m scripts.stats.plot_hists
```
