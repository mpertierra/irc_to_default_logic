import json
from .. import candc_boxer_api
from nltk.tokenize import word_tokenize


def read_definitions(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    definitions = []
    for section_id in data:
        for term in data[section_id]:
            definitions.append(data[section_id][term]["sentence"])
    return definitions

def read_rules(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    rules = {
        "general-rule": [],
        "exceptions": [],
        "special-rules": []
    }
    for section_id in data:
        for level_id in data[section_id]:
            for rule_type in data[section_id][level_id]:
                rules[rule_type].extend(data[section_id][level_id][rule_type])
    return rules

def count_crashes(ccboxer, sentences):
    crashed_token_counts = []
    for sentence in sentences:
        try:
            ccboxer.interpret([sentence])
        except candc_boxer_api.CCBoxerAPIException:
            crashed_token_counts.append(len(word_tokenize(sentence)))
    return crashed_token_counts

def main(args):
    ccboxer = candc_boxer_api.CCBoxerAPI()
    all_crashed_token_counts = {
        "definitions": [],
        "rules": {
            "general-rule": [],
            "exceptions": [],
            "special-rules": []
        }
    }

    definitions = read_definitions(args.definitions_filepath)
    print("Total number of definitions: {}".format(len(definitions)))
    crashed_token_counts = count_crashes(ccboxer, definitions)
    print("Total number of definitions that cause C&C/Boxer crash: {}".format(len(crashed_token_counts)))
    all_crashed_token_counts["definitions"] = crashed_token_counts

    print("*"*25)

    all_rules = read_rules(args.rules_filepath)
    total_crash_count = 0
    for rule_type in all_rules:
        rules = all_rules[rule_type]
        crashed_token_counts = count_crashes(ccboxer, rules)
        print("Total number of rules of type {}: {}".format(rule_type, len(rules)))
        print("Total number of rules of type {} that cause C&C/Boxer crash: {}".format(rule_type, len(crashed_token_counts)))
        all_crashed_token_counts["rules"][rule_type] = crashed_token_counts
        total_crash_count += len(crashed_token_counts)
    print("Total number of rules: {}".format(sum([len(rules) for rules in all_rules.values()])))
    print("Total number of rules that cause C&C/Boxer crash: {}".format(total_crash_count))

    with open(args.output_file, 'w') as f:
        json.dump(all_crashed_token_counts, f, indent=4, sort_keys=True, encoding="UTF-8")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate counts on definitions & rules in Internal Revenue Code " + \
                                                 "that cause C&C/Boxer pipeline to crash.")
    parser.add_argument("--output-file",
                        type=str,
                        default="semparsing_stats.json")
    parser.add_argument("--definitions-filepath",
                        type=str,
                        default="definition_stats/definitions.json")
    parser.add_argument("--rules-filepath",
                        type=str,
                        default="rule_stats/rules.json")
    args = parser.parse_args()
    main(args)