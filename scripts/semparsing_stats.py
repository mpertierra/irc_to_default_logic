import json
import candc_boxer_api


def read_definitions(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    definitions = []
    for section_id in data:
        for term in data[section_id]:
            definitions.append(data[section_id][term])
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
    count = 0
    for sentence in sentences:
        try:
            ccboxer.interpret([sentence])
        except candc_boxer_api.CCBoxerAPIException:
            count += 1
    return count

def main(args):
    ccboxer = candc_boxer_api.CCBoxerAPI()

    definitions = read_definitions(args.definitions_filepath)
    print("Total number of definitions: {}".format(len(definitions)))
    crash_count = count_crashes(ccboxer, definitions)
    print("Total number of definitions that cause C&C/Boxer crash: {}".format(crash_count))

    print("*"*25)

    all_rules = read_rules(args.rules_filepath)
    total_crash_count = 0
    for rule_type in all_rules:
        rules = all_rules[rule_type]
        crash_count = count_crashes(ccboxer, rules)
        print("Total number of rules of type {}: {}".format(rule_type, len(rules)))
        print("Total number of rules of type {} that cause C&C/Boxer crash: {}".format(rule_type, crash_count))
        total_crash_count += crash_count
    print("Total number of rules: {}".format(sum([len(rules) for rules in all_rules.values()])))
    print("Total number of rules that cause C&C/Boxer crash: {}".format(total_crash_count))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate counts on definitions & rules in Internal Revenue Code " + \
                                                 "that cause C&C/Boxer pipeline to crash.")
    parser.add_argument("--definitions-filepath",
                        type=str,
                        default="definition_stats/definitions.json")
    parser.add_argument("--rules-filepath",
                        type=str,
                        default="rule_stats/rules.json")
    args = parser.parse_args()
    main(args)