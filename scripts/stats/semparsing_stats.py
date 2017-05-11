import json
from .. import candc_boxer_api
from nltk.tokenize import word_tokenize


def count_definition_crashes(ccboxer, definitions):
    crashed_token_counts = dict()
    total_section_crash_count = 0
    total_num_definitions = 0
    total_num_crashes = 0
    for section_id in definitions:
        section_definitions = definitions[section_id]
        sentences = [section_definitions[term]["sentence"] for term in section_definitions]
        token_counts = count_crashes(ccboxer, sentences)
        crashed_token_counts[section_id] = token_counts
        if len(token_counts) > 0:
            total_section_crash_count += 1
        total_num_crashes += len(token_counts)
        total_num_definitions += len(sentences)
    print("Total number of sections with definitions: {}".format(len(definitions)))
    print("Total number of sections with crashes for definitions: {}".format(total_section_crash_count))
    print("Total number of definitions: {}".format(total_num_definitions))
    print("Total number of definitions that cause C&C/Boxer crash: {}".format(total_num_crashes))
    return crashed_token_counts

def count_rule_crashes(ccboxer, rules):
    crashed_token_counts = {
        "general-rule": dict(),
        "exceptions": dict(),
        "special-rules": dict()
    }
    total_num_rules = {
        "general-rule": 0,
        "exceptions": 0,
        "special-rules": 0
    }
    total_num_crashes = {
        "general-rule": 0,
        "exceptions": 0,
        "special-rules": 0
    }
    total_section_crash_count = {
        "general-rule": {"total": 0, "crash": 0},
        "exceptions": {"total": 0, "crash": 0},
        "special-rules": {"total": 0, "crash": 0}
    }
    for section_id in rules:
        section_rules = {
            "general-rule": [],
            "exceptions": [],
            "special-rules": []
        }
        for level_id in rules[section_id]:
            level_rules = rules[section_id][level_id]
            for rule_type in level_rules:
                section_rules[rule_type].extend(level_rules[rule_type])
        for rule_type in section_rules:
            sentences = section_rules[rule_type]
            token_counts = count_crashes(ccboxer, sentences)
            crashed_token_counts[rule_type][section_id] = token_counts
            if len(sentences) > 0:
                total_section_crash_count[rule_type]["total"] += 1
            if len(token_counts) > 0:
                total_section_crash_count[rule_type]["crash"] += 1
            total_num_crashes[rule_type] += len(token_counts)
            total_num_rules[rule_type] += len(sentences)
    for rule_type in total_num_rules:
        print("Total number of sections with rules of type {}: {}".format(rule_type, total_section_crash_count[rule_type]["total"]))
        print("Total number of sections with crashes for rules of type {}: {}".format(rule_type, total_section_crash_count[rule_type]["crash"]))
        print("Total number of rules of type {}: {}".format(rule_type, total_num_rules[rule_type]))
        print("Total number of rules of type {} that cause C&C/Boxer crash: {}".format(rule_type, total_num_crashes[rule_type]))
    print("Total number of rules: {}".format(sum(total_num_rules.values())))
    print("Total number of rules that cause C&C/Boxer crash: {}".format(sum(total_num_crashes.values())))
    return crashed_token_counts

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
    all_crashed_token_counts = dict()

    with open(args.definitions_filepath, 'r') as f:
        definitions = json.load(f)

    with open(args.rules_filepath, 'r') as f:
        rules = json.load(f)

    all_crashed_token_counts["definitions"] = count_definition_crashes(ccboxer, definitions)

    print("*"*25)

    all_crashed_token_counts["rules"] = count_rule_crashes(ccboxer, rules)

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