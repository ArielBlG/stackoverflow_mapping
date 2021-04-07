import nltk
import spacy
from spacy import displacy
from supar import Parser
import re

nlp = spacy.load("en_core_web_sm")
parser = Parser.load('crf-con-en')


class ExtractText:

    # def temp_func(self):
    #     sent = [('I', 'PRP'), ('am', 'VBP'), ('trying', 'VBG'), ('to', 'TO'), ('create', 'VB'), ('a', 'DT'), ('parent', 'NN'), ('ArrayList', 'NNP'), ('which', 'WDT'), ('contains', 'VBZ'), ('a', 'DT'), ('sub', 'JJ'), ('ArrayList', 'NNP'), ('for', 'IN'), ('each', 'DT'), ('of', 'IN'), ('its', 'PRP$'), ('index', 'NN'), ('.', '.')]
    #     scnd_sent = [('My', 'PRP$'), ('code', 'NN'), ('involves', 'VBZ'), ('filling', 'VBG'), ('the', 'DT'), ('sub', 'NN'), ('lists', 'NNS'), ('by', 'IN'), ('using', 'VBG'), ('Scanner', 'NNP'), ('Input', 'NNP'), ('.', '.')]
    #     thrd_sent = [('Input', 'NNP'), ('Description', 'NNP'), (':', ':'), ('The', 'DT'), ('first', 'JJ'), ('integer', 'NN'), ('inputed', 'VBN'), ('tells', 'NNS'), ('us', 'PRP'), ('how', 'WRB'), ('many', 'JJ'), ('sub', 'JJ'), ('ArrayLists', 'NNS'), ('we', 'PRP'), ('are', 'VBP'), ('going', 'VBG'), ('to', 'TO'), ('make', 'VB'), (',', ','), ('this', 'DT'), ('could', 'MD'), ('also', 'RB'), ('be', 'VB'), ('seen', 'VBN'), ('as', 'IN'), ('the', 'DT'), ('size', 'NN'), ('of', 'IN'), ('the', 'DT'), ('parent', 'NN'), ('ArrayList', 'NNP'), ('or', 'CC'), ('as', 'IN'), ('how', 'WRB'), ('many', 'JJ'), ('lines', 'NNS'), ('of', 'IN'), ('input', 'NN'), ('are', 'VBP'), ('going', 'VBG'), ('to', 'TO'), ('follow', 'VB'), ('.', '.')]
    #     grammar = '''
    #          NP: {<DT>? <JJ>* <NN.*>*} # NP
    #          PN: {<NP><PRP>} # PN -> NP PRP
    #          P: {<IN>}           # Preposition
    #          V: {<V.*><V.*>?}          # Verb
    #             }<V><V.*>*{
    #          PP: {<P><PRP.*>?<NP>}      # PP -> P NP
    #          VP: {<V> <PP|NP|PN>+}  # VP -> V (NP|PP|PN)+
    #          CV: {<VP><WDT|P><VP>*} # CW -> VP W VP : connected verbs
    #          NV: {<NP><V.*>+} # NP -> V
    #          TV: {<.*>?<TO><V.*>} # something -> TO -> Verb
    #          '''
    #     #
    #     cp = nltk.RegexpParser(grammar, loop=7)
    #     result = cp.parse(sent)
    #     print(result)
    #     print("------------------------------------------------")
    #     cp = nltk.RegexpParser(grammar, loop=7)
    #     result = cp.parse(scnd_sent)
    #     print(result)
    #     print("------------------------------------------------")
    #     cp = nltk.RegexpParser(grammar, loop=7)
    #     result = cp.parse(thrd_sent)
    #     print(result)
    def temp_func(self):

        doc1 = "How to put Multiple ArrayLists inside an ArrayList Java"
        # doc2 = 'How to sort a list of objects by a certain value within the object'
        doc2 = "I am trying to create a parent ArrayList which contains a sub ArrayList for each of its index"
        doc3 = "My code involves filling the sub lists by using Scanner Input."
        doc4 = "The first integer inputed tells us how many sub ArrayLists we are going to make," \
               " this could also be, seen as the size of the parent ArrayList or as how many lines " \
               "of input are going to follow."
        doc5 = "all lines after this point will be the integers we want to store within each sub arraylist."
        doc6 = "As mentioned earlier, add for lists don't return a list but rather a boolean."

        # doc1 = "First thing, do not initialize your subList while declaration as your are again" \
        #        " initializing it in for loop."
        # doc2 = "So, object is never used."
        # doc3 = "to your question, why are you doing q.nextInt() once in a loop"
        # doc4 = "It means you are not expecting more than one number per sublist."
        # doc5 = "As mentioned by others you cannot add sublist to parentList as you have done."
        # doc6 = "I have also changed delimiter to , instead of space."
        # doc7 = "I have modified the code keeping these things in mind."

        doc1_nlp = nlp(doc1)
        doc2_nlp = nlp(doc2)
        doc3_nlp = nlp(doc3)
        doc4_nlp = nlp(doc4)
        doc5_nlp = nlp(doc5)
        doc6_nlp = nlp(doc6)
        # doc7_nlp = nlp(doc7)

        docs = [ doc2, doc3, doc4, doc5, doc6]
        docs_nlp = [doc1_nlp, doc2_nlp, doc3_nlp, doc4_nlp, doc5_nlp, doc6_nlp]
        # displacy.serve(doc4_nlp, style="dep")

        # for doc in docs_nlp:
        #     for token in doc:
        #         if token.dep_ == "ROOT":
        #             self.print_rec(token)
        #     print(self.txt)
        #     self.txt = ""

        for doc in docs:
            text = nltk.word_tokenize(doc)
            dataset = parser.predict([text], verbose=False)
            print(" ")
            self.extract_trees(dataset.trees[0])
            print(f"trees:\n{dataset.trees[0]}")
            print("------------------------------------------------------------------------------------------")

    def extract_trees(self, tree):
        # a = tree.height()
        if isinstance(tree, str):
            return
        if tree.label() == "NP" or tree.label() == "PP":
            print_str = str(tree)
            print_str = print_str.replace("(", "")
            print_str = print_str.replace(")", "")
            print_str = print_str.replace("_", "")
            print_str = print_str.replace("NP", "")
            print_str = print_str.replace("PP", "")
            print_str = print_str.replace("VP", "")
            print_str = print_str.replace("S", "")
            print_str = print_str.replace("\n ", "")
            print_str = print_str.replace("\t", "")
            print_str = print_str.replace("BAR", "")
            print_str = print_str.replace("WH", "")
            if not print_str.isspace():
                print(print_str)
            return
        for index in range(0, tree.__len__()):
            sub_tree = tree[index]
            if not isinstance(sub_tree, str):
                self.extract_trees(sub_tree)

    def print_rec(self, token):

        # self.txt += ' '.join([ctoken.text for ctoken in token.lefts]) + ' ' + token.text + ' '

        for left_tok in token.lefts:
            self.print_rec(left_tok)

        self.txt += ' ' + token.text
        if token.dep_ == 'prep' or token.dep_ == "ROOT" or token.pos_ == "VERB":
            self.txt += '-->'

        for right_tok in token.rights:
            self.print_rec(right_tok)

    def __init__(self):
        # self.temp_func()
        self.txt = ""

# tokens = nltk.word_tokenize(sentence)
# sentence = """This solution also very similar to other posts except that it uses System.arrayCopy to copy the remaining array elements."""
