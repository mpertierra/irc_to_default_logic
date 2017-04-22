import re
from irc_crawler import IRCCrawler
from collections import OrderedDict


def only_letters(text):
    pattern = re.compile("[^a-zA-Z]+", re.UNICODE)
    return pattern.sub("", text)

def extract_rules(level):
    rules = OrderedDict()
    for slevel in level.preorder_transversal():
        if slevel.heading is None:
            continue
        heading = only_letters(slevel.heading).lower()
        level_rules = OrderedDict()
        if heading == "generalrule":
            level_rules["general-rule"] = slevel.get_sentences()
        elif heading == "exceptions":
            level_rules["exceptions"] = slevel.get_sentences()
        elif heading == "specialrules":
            level_rules["special-rules"] = slevel.get_sentences()
        if len(level_rules) > 0:
            rules[slevel.id.val] = level_rules
    return rules

def main(args):
    crawler = IRCCrawler()
    level = crawler.get_level(args.level_id)

    rules = extract_rules(level)
    if len(rules) == 0:
        print("Info: No rules found.")
        return

    for level_id in rules:
        for rule_type in rules[level_id]:
            for rule in rules[level_id][rule_type]:
                print(u"Level ID:  {}".format(level_id))
                print(u"Rule type: {}".format(rule_type))
                print(u"Rule:      {}".format(rule))
                print(u"*************")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract rules from parts of the Internal Revenue Code.")
    parser.add_argument("--level-id",
                        type=str,
                        default="s163",
                        help="Specifies the level (section, subsection, paragraph, etc.) to find. " + \
                              "Should have pattern s[section]/[subsection]/[paragraph]/[subparagraph]/[clause]/[subclause]/[item]. " + \
                              "For example, 's163/h/1' specifies section 163, subsection h, paragraph 1.")
    args = parser.parse_args()
    main(args)