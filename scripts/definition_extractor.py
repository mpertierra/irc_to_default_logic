# This Python file uses the following encoding: UTF-8
import re
from irc_crawler import IRCCrawler

DEFINITION_TYPES = [
    u"means",
    u"includes",
    u"does not include",
    u"has the meaning",
    u"shall include",
    u"shall not include"
]
TERM_REGEX = re.compile(ur"the term (?:(“[^”]+”)|(‘[^’]+’)) (?:{0})".format(u"|".join(DEFINITION_TYPES)), re.UNICODE | re.IGNORECASE)


def get_term_regex(term):
    definition_types_pattern = ur"({0})".format(u"|".join(DEFINITION_TYPES))
    return re.compile(ur"the term (?:“{0}”|‘{0}’) {1}(.*)".format(term, definition_types_pattern), re.UNICODE | re.IGNORECASE)

def extract_defined_terms(level):
    text = u'\n'.join(level.get_sentences())
    defined_terms = []
    matches = TERM_REGEX.findall(text)
    for group1, group2 in matches:
        term = None
        if group1 != '':
            assert group2 == ''
            assert group1.startswith(u"“") and group1.endswith(u"”")
            term = group1[1:-1]
        if group2 != '':
            assert group1 == ''
            assert group2.startswith(u"‘") and group2.endswith(u"’")
            term = group2[1:-1]
        assert term is not None and len(term) > 0
        defined_terms.append(term)
    return defined_terms

def extract_definitions(level, defined_terms):
    definition_fol_template = u"all x.({0}{1}(x) -> {2}{3}(x))"
    definitions = []
    sentences = level.get_sentences()
    for sentence in sentences:
        for defined_term in defined_terms:
            term_def_regex = get_term_regex(defined_term)
            matches = term_def_regex.findall(sentence)
            if len(matches) == 0: continue
            assert len(matches) == 1
            def_type, rest = matches[0]
            assert def_type in DEFINITION_TYPES
            assert len(rest) > 0
            for other_term in defined_terms:
                if other_term == defined_term: continue
                if other_term in rest:
                    other_term_sign = ""
                    if "not" in def_type:
                        other_term_sign = "-"
                    other_term_predicate = term_to_predicate(other_term)
                    defined_term_sign = ""
                    if "other than" in rest or "except" in rest:
                        defined_term_sign = "-"
                    defined_term_predicate = term_to_predicate(defined_term)
                    definition_fol = definition_fol_template.format(
                        other_term_sign,
                        other_term_predicate,
                        defined_term_sign,
                        defined_term_predicate
                    )
                    definitions.append(definition_fol)
    return definitions

def term_to_predicate(term):
    predicate = term.strip().replace(" ", "_SPACE_").replace("-", "_DASH_").replace(",", "_COMMA_")
    if predicate in ["and", "or", "implies", "iff", "some", "exists", "exist", "all", "forall", "not"]:
        predicate = predicate.upper()
    if len(predicate) == 1:
        predicate = "_{0}_".format(predicate)
    return predicate

def main(args):
    crawler = IRCCrawler()
    level = crawler.get_level(args.level_id)

    defined_terms = extract_defined_terms(level)
    if len(defined_terms) == 0:
        print("Info: No term definitions found.")
        return
    definitions = extract_definitions(level, defined_terms)

    print("*****Defined terms*****")
    for term in defined_terms: print(term)
    print("*****Definitions*****")
    for d in definitions: print(d)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract definitions from parts of the Internal Revenue Code.")
    parser.add_argument("--level-id",
                        type=str,
                        default="s163/h",
                        help="Specifies the level (section, subsection, paragraph, etc.) to find. " + \
                              "Should have pattern s[section]/[subsection]/[paragraph]/[subparagraph]/[clause]/[subclause]/[item]. " + \
                              "For example, 's163/h/1' specifies section 163, subsection h, paragraph 1.")
    args = parser.parse_args()
    main(args)
