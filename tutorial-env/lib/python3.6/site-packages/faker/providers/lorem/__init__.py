from .. import BaseProvider

localized = True

# 'Latin' is the default locale
default_locale = 'la'


class Provider(BaseProvider):
    """Will provide methods to retrieve lorem content

    Attributes:
        sentence_punctuation (str): End of sentence punctuation
        word_connector (str): Default connector between words

    Methods:
        word: Generate a random word
        words: Generate a list containing random words
        sentence: Generate a random sentence
        sentences: Generate a list containing sentences
        paragraph: Generate a single paragraph
        paragraphs: Generate many paragraphs
        text: Generate a text string.
    """
    word_connector = ' '
    sentence_punctuation = '.'

    def words(self, nb=3, ext_word_list=None, unique=False):
        """
        :returns: An array of random words. for example: ['Lorem', 'ipsum', 'dolor']

        Keyword arguments:
        :param nb: how many words to return
        :param ext_word_list: a list of words you would like to have instead of
            'Lorem ipsum'
        :param unique: If True, the returned word list will contain unique words

        :rtype: list
        """
        word_list = ext_word_list if ext_word_list else self.word_list
        if unique:
            return self.random_sample(word_list, length=nb)
        return self.random_choices(word_list, length=nb)

    def word(self, ext_word_list=None):
        """
        :returns: A random word, eg: 'lorem'

        :param ext_word_list: a list of words you would like to have instead of
            'Lorem ipsum'

        :rtype: str
        """
        return self.words(1, ext_word_list)[0]

    def sentence(self, nb_words=6, variable_nb_words=True, ext_word_list=None):
        """
        Generate a random sentence
        :example 'Lorem ipsum dolor sit amet.'

        :param nb_words: around how many words the sentence should contain
        :param variable_nb_words: set to false if you want exactly ``nb``
            words returned, otherwise the result may include a number of words
            of ``nb`` +/-40% (with a minimum of 1)
        :param ext_word_list: a list of words you would like to have instead of
            'Lorem ipsum'.

        :rtype: str
        """
        if nb_words <= 0:
            return ''

        if variable_nb_words:
            nb_words = self.randomize_nb_elements(nb_words, min=1)

        words = self.words(nb=nb_words, ext_word_list=ext_word_list)
        words[0] = words[0].title()

        return self.word_connector.join(words) + self.sentence_punctuation

    def sentences(self, nb=3, ext_word_list=None):
        """
        Generate an array of sentences
        :example ['Lorem ipsum dolor sit amet.', 'Consectetur adipisicing eli.']

        Keyword arguments:
        :param nb: how many sentences to return
        :param ext_word_list: a list of words you would like to have instead of
            'Lorem ipsum'.

        :rtype: list
        """
        return [self.sentence(ext_word_list=ext_word_list)
                for _ in range(0, nb)]

    def paragraph(
            self,
            nb_sentences=3,
            variable_nb_sentences=True,
            ext_word_list=None):
        """
        :returns: A single paragraph. For example: 'Sapiente sunt omnis. Ut
            pariatur ad autem ducimus et. Voluptas rem voluptas sint modi dolorem amet.'

        Keyword arguments:
        :param nb_sentences: around how many sentences the paragraph should contain
        :param variable_nb_sentences: set to false if you want exactly ``nb``
            sentences returned, otherwise the result may include a number of
            sentences of ``nb`` +/-40% (with a minimum of 1)
        :param ext_word_list: a list of words you would like to have instead of
            'Lorem ipsum'.

        :rtype: str
        """
        if nb_sentences <= 0:
            return ''

        if variable_nb_sentences:
            nb_sentences = self.randomize_nb_elements(nb_sentences, min=1)

        para = self.word_connector.join(self.sentences(
            nb_sentences, ext_word_list=ext_word_list,
        ))

        return para

    def paragraphs(self, nb=3, ext_word_list=None):
        """
        Generate an array of paragraphs
        :example [paragraph1, paragraph2, paragraph3]
        :param nb: how many paragraphs to return
        :param ext_word_list: a list of words you would like to have instead of
            'Lorem ipsum'.

        :rtype: list
        """

        return [self.paragraph(ext_word_list=ext_word_list)
                for _ in range(0, nb)]

    def text(self, max_nb_chars=200, ext_word_list=None):
        """
        Generate a text string.
        Depending on the ``max_nb_chars, returns a string made of words, sentences, or paragraphs.
        :example 'Sapiente sunt omnis. Ut pariatur ad autem ducimus et. Voluptas rem voluptas sint modi dolorem amet.'

        Keyword arguments:
        :param max_nb_chars: Maximum number of characters the text should contain (minimum 5)
        :param ext_word_list: a list of words you would like to have instead of 'Lorem ipsum'.

        :rtype str
        """
        text = []
        if max_nb_chars < 5:
            raise ValueError(
                'text() can only generate text of at least 5 characters')

        if max_nb_chars < 25:
            # join words
            while not text:
                size = 0
                # determine how many words are needed to reach the $max_nb_chars
                # once;
                while size < max_nb_chars:
                    word = (self.word_connector if size else '') + \
                        self.word(ext_word_list=ext_word_list)
                    text.append(word)
                    size += len(word)
                text.pop()
            text[0] = text[0][0].upper() + text[0][1:]
            last_index = len(text) - 1
            text[last_index] += self.sentence_punctuation
        elif max_nb_chars < 100:
            # join sentences
            while not text:
                size = 0
                # determine how many sentences are needed to reach the
                # $max_nb_chars once
                while size < max_nb_chars:
                    sentence = (self.word_connector if size else '') + \
                        self.sentence(ext_word_list=ext_word_list)
                    text.append(sentence)
                    size += len(sentence)
                text.pop()
        else:
            # join paragraphs
            while not text:
                size = 0
                # determine how many paragraphs are needed to reach the
                # $max_nb_chars once
                while size < max_nb_chars:
                    paragraph = ('\n' if size else '') + \
                        self.paragraph(ext_word_list=ext_word_list)
                    text.append(paragraph)
                    size += len(paragraph)
                text.pop()

        return "".join(text)
