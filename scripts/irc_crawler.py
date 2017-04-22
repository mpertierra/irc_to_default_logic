# This Python file uses the following encoding: UTF-8
from os.path import dirname, join, realpath
from lxml import etree
from collections import OrderedDict
import re
from nltk.tokenize import sent_tokenize, word_tokenize


IRC_XML_FILEPATH = join(dirname(dirname(realpath(__file__))), "irc/xml/irc.xml")
TAGS = ["section", "subsection", "paragraph", "subparagraph", "clause", "subclause", "item", "subitem", "subsubitem"]


class LevelId:
    LEVEL_ID_PATTERN = re.compile(u"^s[^/]+(/[a-zA-Z0-9]+)*$", re.UNICODE)

    @staticmethod
    def _validate(val):
        assert isinstance(val, unicode), u"Non-unicode level id: {0}".format(val)
        assert LevelId.LEVEL_ID_PATTERN.match(val), u"Invalid level id: {0}".format(val)

    def __init__(self, val):
        val = unicode(val)
        LevelId._validate(val)
        self.val = val

    def get_section_id(self):
        return self.val.split(u'/')[0]

    def get_section_num(self):
        return self.get_section_id()[1:]

    def get_depth(self):
        return len(self.val.split(u'/')) - 1

    def get_num(self):
        if self.get_depth() == 0:
            return self.get_section_num()
        return self.val.split(u'/')[-1]

    def __unicode__(self):
        return self.val

    def __str__(self):
        return unicode(self).encode("UTF-8")

class LevelHasNoIdException(Exception):
    pass

class LevelDoesNotExistException(Exception):
    pass

class Level:
    @staticmethod
    def _validate(id, tag, num, heading, chapeau, content, sublevels, continuation):
        assert isinstance(id, LevelId)
        assert tag in TAGS, u"Unknown tag: {0}".format(tag)
        assert num == id.get_num()
        for s in [heading, chapeau, continuation, content]:
            assert s is None or isinstance(s, unicode), "Non-unicode text: {0}".format(s)
        assert isinstance(sublevels, OrderedDict)

    def __init__(self, id, tag, num, heading, chapeau, content, sublevels, continuation):
        Level._validate(id, tag, num, heading, chapeau, content, sublevels, continuation)
        self.id = id
        self.tag = tag
        self.num = num
        self.heading = heading
        self.chapeau = chapeau
        self.content = content
        self.sublevels = sublevels
        self.continuation = continuation
        # Lazy evaluation
        self._sentence_fragments = None
        self._sentences = None
        self._avg_tokens_per_sentence = None
        self._total_token_count = None

    def get_total_token_count(self, word_tokenizer=word_tokenize):
        if self._total_token_count is None:
            total_token_count = 0
            for sent_fragment in self.get_sentence_fragments():
                total_token_count += word_tokenizer(sent_fragment)
            self._total_token_count = total_token_count
        return self._total_token_count

    def get_average_tokens_per_sentence(self, word_tokenizer=word_tokenize):
        if self._avg_tokens_per_sentence is None:
            sentences = self.get_sentences()
            num_sentences = len(sentences)
            num_tokens = 0
            for sent in sentences:
                num_tokens += len(word_tokenizer(sent))
            if num_sentences == 0:
                self._avg_tokens_per_sentence = 0
            else:
                self._avg_tokens_per_sentence = num_tokens / float(num_sentences)
        return self._avg_tokens_per_sentence

    def get_sentences(self, sentence_tokenizer=sent_tokenize):
        if self._sentences is None:
            sent_fragments = self.get_sentence_fragments()
            level_str = u" ".join(sent_fragments)
            self._sentences = sentence_tokenizer(level_str)
        return self._sentences

    def get_sentence_fragments(self):
        if self._sentence_fragments is None:
            sent_fragments = []
            if self.chapeau is not None:
                sent_fragments.append(self.chapeau)
            if self.content is not None:
                sent_fragments.append(self.content)
            for c in self.sublevels.values():
                sublevel, continuation = c[0], c[1]
                sent_fragments.extend(sublevel.get_sentence_fragments())
                if continuation is not None:
                    sent_fragments.append(continuation)
            if self.continuation is not None:
                sent_fragments.append(self.continuation)
            self._sentence_fragments = sent_fragments
        return self._sentence_fragments

    def preorder_transversal(self):
        yield self
        for c in self.sublevels.values():
            sublevel = c[0]
            for l in sublevel.preorder_transversal():
                yield l

    def __unicode__(self):
        return u'\n'.join(self.get_sentences())

    def __str__(self):
        return unicode(self).encode("UTF-8")


class IRCCrawler:
    def __init__(self, default_namespace="USLM", debug=False):
        self.tree = etree.parse(IRC_XML_FILEPATH)
        self.root = self.tree.getroot()
        self.default_namespace = default_namespace
        self.nsmap = self.root.nsmap
        self.nsmap[default_namespace] = self.nsmap.pop(None)
        self.debug = debug

    def _namespace_prefix(self):
        return "{{{0}}}".format(self.nsmap[self.default_namespace])

    def _stringify_node(self, node):
        return etree.tostring(node, method="text", encoding="UTF-8").strip().decode("UTF-8")

    def _get_level_node(self, level_id):
        assert isinstance(level_id, LevelId)
        xpath_expression = "//{0}:*[@identifier='/us/usc/t26/{1}']".format(self.default_namespace, level_id)
        nodes = self.root.xpath(xpath_expression, namespaces=self.nsmap)
        assert len(nodes) <= 1
        if len(nodes) == 0:
            raise LevelDoesNotExistException()
        return nodes[0]

    def _parse_level(self, node):
        if node.get("identifier") is None:
            # Happens for some quoted sections that appear in the "notes"
            raise LevelHasNoIdException()
        identifier_prefix = u"/us/usc/t26/"
        assert node.get("identifier").startswith(identifier_prefix)
        id = LevelId(node.get("identifier").replace(identifier_prefix, '', 1))
        ns_prefix = self._namespace_prefix()
        assert node.tag.startswith(ns_prefix)
        tag = node.tag.replace(ns_prefix, '', 1)
        num = None
        level = {"heading": None, "chapeau": None, "content": None, "continuation": None}
        sublevels = OrderedDict()
        for c in node:
            c_tag = c.tag.replace(ns_prefix, '', 1)
            if c_tag == "num":
                assert num is None, u"Repeated num in level {}".format(id)
                num = c.get("value")
            elif c_tag in level:
                if c_tag == "continuation":
                    continuation = self._stringify_node(c)
                    if len(sublevels) == 0:
                        assert level["continuation"] is None
                        level["continuation"] = continuation
                    else:
                        # Continuations can be "sandwiched" between sublevels
                        # See 10.4 in http://xml.house.gov/schemas/uslm/1.0/USLM-User-Guide.pdf
                        prev_sublevel_num = next(reversed(sublevels))
                        prev_sublevel_and_continuation = sublevels[prev_sublevel_num]
                        if prev_sublevel_and_continuation[1] is None:
                            prev_sublevel_and_continuation[1] = continuation
                        else:
                            assert level["continuation"] is None
                            level["continuation"] = continuation
                else:
                    level[c_tag] = self._stringify_node(c)
            elif c_tag in TAGS:
                sublevel = self._parse_level(c)
                sublevel_num = sublevel.num
                # Apparently, there exist some levels with the same name
                while sublevel_num in sublevels:
                    sublevel_num += "?"
                # First element is sublevel, second element is continuation
                sublevels[sublevel_num] = [sublevel, None]
            elif self.debug:
                print(u"Warning: Skipping element with tag {0}".format(c.tag))
        return Level(id, tag, num, level["heading"], level["chapeau"], level["content"], sublevels, level["continuation"])

    def _iterate_over_nodes(self, tags=[]):
        for t in tags:
            assert t in TAGS, u"Unknown tag: {}".format(t)
        tags = ["{0}{1}".format(self._namespace_prefix(), t) for t in tags]
        for node in self.root.iter(*tags):
            yield node

    def get_level(self, level_id):
        level_id = LevelId(level_id)
        level_node = self._get_level_node(level_id)
        level = self._parse_level(level_node)
        return level

    def iterate_over_sections(self):
        for node in self._iterate_over_nodes(tags=["section"]):
            if node.get("status") in ["repealed", "omitted"]:
                # Skip "repealed" (288 counted) and "omitted" (2 counted) sections
                # Other statuses are "renumbered" (17 counted) and "reserved" (2 counted)
                # All other sections have no status.
                continue
            try:
                level = self._parse_level(node)
            except LevelHasNoIdException:
                continue
            yield level

    # def find_levels_by_text(self, text, scope_level_id, tag="*"):
    #     text = text.lower()
    #     scope_level_id = LevelId(scope_level_id)
    #     scope_node = self._get_level_node(scope_level_id)
    #     tag = "{0}:{1}".format(self.default_namespace, tag)
    #     to_lowercase = "translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
    #     xpath_expression = ".//{0}[text()[contains({1}, '{2}')]]".format(tag, to_lowercase, text)
    #     nodes = scope_node.xpath(xpath_expression, namespaces=self.nsmap)
    #     levels = []
    #     for node in nodes:
    #         level_node = node
    #         while level_node.get("identifier") is None:
    #             level_node = level_node.getparent()
    #         level = self._parse_level(level_node)
    #         levels.append(level)
    #     return levels

def validate_sections(crawler=None):
    if crawler is None:
        crawler = IRCCrawler()
    count = 0
    for section in crawler.iterate_over_sections():
        count += 1
    print("Validated {} sections".format(count))

def get_sections_ordered_by_average_tokens_per_sentence(crawler=None):
    if crawler is None:
        crawler = IRCCrawler()
    section_num_avg_tokens_per_sent_pairs = []
    for section in crawler.iterate_over_sections():
        average_tokens_per_sentence = section.get_average_tokens_per_sentence()
        section_num_avg_tokens_per_sent_pairs.append((section.num, average_tokens_per_sentence))
    section_num_avg_tokens_per_sent_pairs.sort(key=lambda pair: pair[1])
    return section_num_avg_tokens_per_sent_pairs


def main(args):
    crawler = IRCCrawler()
    level = crawler.get_level(args.level_id)
    print(level)
    # levels = crawler.find_levels_by_text("general", args.level_id, tag="heading")
    # for level in levels:
    #     print("*"*5)
    #     print(level)
    # validate_sections(crawler=crawler)
    # print(get_sections_ordered_by_average_tokens_per_sentence(crawler=crawler)[:50])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crawl the Internal Revenue Code.")
    parser.add_argument("--level-id",
                        type=str,
                        default="s163/h",
                        help="Specifies the level (section, subsection, paragraph, etc.) to find. " + \
                              "Should have pattern s[section]/[subsection]/[paragraph]/[subparagraph]/[clause]/[subclause]/[item]/[subitem]/[subsubitem]. " + \
                              "For example, 's163/h/1' specifies section 163, subsection h, paragraph 1.")
    args = parser.parse_args()
    main(args)


