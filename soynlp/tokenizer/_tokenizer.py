import re
from collections import namedtuple
from pprint import pprint


Token = namedtuple('Token', 'word b e score length')


class RegexTokenizer:
    """
    Split sentence based on type of characters and regex pattern.
    Or it is available to customize RegexTokenizer with my regex patterns.

    Args:
        pipielines (list of re.Pattern or None) :
            The regex patterns will be applied one by one to input string.
            If None, it uses default patterns (number -> Korean -> jaum -> moum -> Alphabet)
    """
    def __init__(self, pipelines=None):
        if pipelines is None:
            pipelines = self._default_pipelines()
        self.pipelines = pipelines
        self.doublewhite_pattern = re.compile('\s+')

    def _default_pipelines(self):
        return [
            re.compile(u'[-+]?\d*[\.]?[\d]+|[-+]?\d+', re.UNICODE),  # number
            re.compile(u'[가-힣]+', re.UNICODE),                      # Korean
            re.compile(u'[ㄱ-ㅎ]+', re.UNICODE),                      # jaum
            re.compile(u'[ㅏ-ㅣ]+', re.UNICODE),                      # moum
            re.compile(u"[a-zA-ZÀ-ÿ]+[[`']{1,1}s]*|[a-zA-ZÀ-ÿ]+", re.UNICODE),  # Alphabet
        ]

    def __call__(self, sentence, flatten=True):
        return self.tokenize(sentence, flatten)

    def tokenize(self, sentence, flatten=True):
        """Split sentence based on type of characters and regex pattern.

        Args:
            sentence (str) : input string
            flatten (Boolean) :
                If True, it returns tokens as form of list of str
                Otherwise, it returns nested list of `Token`

        Returns:
            tokens (list of str or nested list of Token)

        Examples::
            >>> s = 'abc123가나다 alphabet!!3.14한글 hank`s report'
            >>> regex_tokenizer = RegexTokenizer()
            >>> regex_tokenizer.tokenize(s)
            >>> regex_tokenizer(s) # same with above line.
            $ ['abc', '123', '가나다', 'alphabet', '!!', '3.14', '한글', 'hank`s', 'report']

            >>> regex_tokenizer.tokenize(s, flatten=False)
            >>> regex_tokenizer(s, flatten=False)  # same with above line.
            $ [[Token(word='abc', b=0, e=3, score=1, length=3),
                Token(word='123', b=3, e=6, score=1, length=3),
                Token(word='가나다', b=6, e=9, score=1, length=3)],
               [Token(word='alphabet', b=10, e=18, score=1, length=8),
                Token(word='!!', b=18, e=20, score=1, length=2),
                Token(word='3.14', b=20, e=24, score=1, length=4),
                Token(word='한글', b=24, e=26, score=1, length=2)],
               [Token(word='hank`s', b=27, e=33, score=1, length=6)],
               [Token(word='report', b=34, e=40, score=1, length=6)]]
        """
        offset = 0
        tokens = []
        for token in sentence.split():
            tokens.append(self._tokenize(token, offset))
            offset += (len(token) + 1)
        if flatten:
            tokens = [token.word for tokens_in_eojeol in tokens for token in tokens_in_eojeol if token.word]
        return tokens

    def _tokenize(self, s, offset=0):
        # TODO: handle 3.1.2.1
        for pattern in self.pipelines:
            founds = pattern.findall(s)
            if not founds:
                continue
            found = founds.pop(0)
            len_found = len(found)

            s_ = ''
            b = 0
            for i, c in enumerate(s):
                if b > i:
                    continue
                if s[i: i + len_found] == found:
                    s_ += ' %s ' % s[i: i + len_found]
                    b = i + len_found
                    if not founds:
                        s_ += s[b:]
                        break
                    else:
                        found = founds.pop(0)
                        len_found = len(found)
                    continue
                s_ += c
            s = s_
        words = self.doublewhite_pattern.sub(' ', s).strip().split()
        r = len(words[0])
        tokens = [Token(words[0], 0 + offset, r + offset, 1, r)]
        b = tokens[0].e
        for word in words[1:]:
            r = len(word)
            tokens.append(Token(word, b, b + r, 1, r))
            b += r
        return tokens


class LTokenizer:
    """
    Args:
        scores ({str: float}) : {word: score}
        unknown_score (float) : unknown word score

    Examples::
        Without tolerance

            >>> scores = {'파스': 0.65, '파스타': 0.7, '좋아': 0.3}
            >>> ltokenizer = LTokenizer(scores)
            >>> ltokenizer.tokenize('파스타가 좋아요 파스타가좋아요')
            >>> ltokenizer('파스타가 좋아요 파스타가좋아요')  # same with above line
            $ ['파스타', '가', '좋아', '요', '파스타', '가좋아요']

            >>> ltokenizer.tokenize('파스타가 좋아요 파스타가좋아요', flatten=False)
            $ [[Token(word='파스타', b=0, e=3, score=0.7, length=3),
                Token(word='가', b=3, e=4, score=0, length=1)],
               [Token(word='좋아', b=5, e=7, score=0.3, length=2),
                Token(word='요', b=7, e=8, score=0, length=1)],
               [Token(word='파스타', b=9, e=12, score=0.7, length=3),
                Token(word='가좋아요', b=12, e=16, score=0, length=4)]]

        With tolerance

            >>> scores = {'파스': 0.75, '파스타': 0.7, '좋아': 0.3}
            >>> ltokenizer = LTokenizer(scores)
            >>> ltokenizer.tokenize('파스타가 좋아요 파스타가좋아요', tolerance=0.06)
            $ ['파스타', '가', '좋아', '요', '파스타', '가좋아요']

            >>> ltokenizer.tokenize('파스타가 좋아요 파스타가좋아요', tolerance=0.06, flatten=False)
            $ [[Token(word='파스타', b=0, e=3, score=0.7, length=3),
                Token(word='가', b=3, e=4, score=0, length=1)],
               [Token(word='좋아', b=5, e=7, score=0.3, length=2),
                Token(word='요', b=7, e=8, score=0, length=1)],
               [Token(word='파스타', b=9, e=12, score=0.7, length=3),
                Token(word='가좋아요', b=12, e=16, score=0, length=4)]]
    """
    def __init__(self, scores, unknown_score=0.0):
        self.scores = scores
        self.unknown_score = unknown_score

    def __call__(self, sentence, tolerance=0.0, flatten=True, remove_r=False):
        return self.tokenize(sentence, tolerance, flatten, remove_r)

    def tokenize(self, sentence, tolerance=0.0, flatten=True, remove_r=False):
        """
        Args:
            sentence (str) : input string
            tolerance (float) :
                If the difference between the highest and the second highest score
                is less than `tolerance`, this tokenizer choose longer one as word
            flatten (Boolean) :
                If True, it returns tokens as form of list of str
                Otherwise, it returns nested list of `Token`
            remove_r (Boolean) :
                If True, it returns only L parts

        Returns:
            tokens (list of str or nested list of Token)
        """

        def token_to_lr(token):
            """Returns: (score of L, L, R)"""
            n = len(token)
            if n <= 2:
                return (token, '', self.scores.get(l, self.unknown_score))

            candidates = [(token[:e], token[e:]) for e in range(2, n + 1)]
            candidates = [(self.scores.get(l, self.unknown_score), l, r) for l, r in candidates]
            if tolerance > 0:
                max_score = max([c[0] for c in candidates])
                candidates = [c for c in candidates if (max_score - c[0]) <= tolerance]
                best = sorted(candidates, key=lambda x: len(x[1]), reverse=True)[0]
            else:
                best = sorted(candidates, key=lambda x: (x[0], len(x[1])), reverse=True)[0]
            return best

        offset = 0
        tokens = []
        for s in sentence.split():
            score, l, r = token_to_lr(s)
            len_l, len_r = len(l), len(r)
            tokens.append([
                Token(l, offset, offset + len_l, score, len_l),
                Token(r, offset + len_l, offset + len_l + len_r, 0, len_r)
            ])
            offset += (len_l + len_r + 1)

        if remove_r:
            tokens = [l.word for l, r in tokens]

        if (flatten) and (not remove_r):
            tokens = [subtoken.word for token in tokens for subtoken in token if subtoken.length > 0]

        return tokens


class MaxScoreTokenizer:
    def __init__(self, scores, max_length=10, unknown_score=0.0):
        self.scores = scores
        self.max_len = max_length
        self.unknown_score = unknown_score

    def __call__(self, sentence, flatten=True):
        return self.tokenize(sentence, flatten)

    def tokenize(self, sentence, flatten=True):
        """
        Args:
            sentence (str) : input string
            tolerance (float) :
                If the difference between the highest and the second highest score
                is less than `tolerance`, this tokenizer choose longer one as word
            flatten (Boolean) :
                If True, it returns tokens as form of list of str
                Otherwise, it returns nested list of `Token`

        Returns:
            tokens (list of str or nested list of Token)
        """
        offset = 0
        tokens = []
        for s in sentence.split():
            tokens.append(self._recursive_tokenize(s, offset))
            offset += (len(s) + 1)
        if flatten:
            tokens = [subtoken.word for token in tokens for subtoken in token]
        return tokens

    def _recursive_tokenize(self, s, offset):
        length = len(s)
        if length <= 2:
            token = Token(
                s,
                offset,
                offset + length,
                self.scores.get(token, self.unknown_score),
                length
            )
            return [token]

        scored = self._initialize(s, length, offset)
        result = self._find(scored)
        # post processing
        # TODO: offset 적용
        adds = self._add_inter_subtokens(s, result, offset)
        if result[-1][2] != length:
            adds += self._add_last_subtoken(s, result)
        if result[0][1] != 0:
            adds += self._add_first_subtoken(s, result)

        return sorted(result + adds, key=lambda x: x[1])

    def _initialize(self, token, length, offset=0):
        max_r = min(length, self.max_len)
        scored = []
        for b in range(0, length - 1):
            for r in range(2, max_r + 1):
                e = b + r
                if e > length:
                    continue
                subtoken = token[b: e]
                score = self.scores.get(subtoken, self.unknown_score)
                scored.append(Token(subtoken, offset + b, offset + e, score, r))
        return sorted(scored, key=lambda x:(-x.score, -x.length, x.b))

    def _find(self, scored):
        result = []
        num_iter = 0
        while scored:
            word, b, e, score, r = scored.pop(0)
            result.append(Token(word, b, e, score, r))
            if not scored:
                break
            removals = []
            for i, (_1, b_, e_, _2, _3) in enumerate(scored):
                if (b_ < e and b < e_) or (b_ < e and e_ > b):
                    removals.append(i)
            for i in reversed(removals):
                del scored[i]
            num_iter += 1
            if num_iter > 100:
                break
        return sorted(result, key=lambda x: x.b)

    def _add_inter_subtokens(self, token, result, offset=0):
        adds = []
        for i, base in enumerate(result[: -1]):
            if base[2] == result[i + 1][1]:
                continue
            b = base[2] - offset
            e = result[i + 1][1] - offset
            subtoken = token[b: e]
            adds.append(Token(subtoken, b, e, self.unknown_score, e - b))
        return adds

    def _add_first_subtoken(self, token, result, offset=0):
        e = result[0][1]
        subtoken = token[0: e - offset]
        score = self.scores.get(subtoken, self.unknown_score)
        return [Token(subtoken, offset, e, score, e - offset)]
    
    def _add_last_subtoken(self, token, result, offset=0):
        b = result[-1][2]
        subtoken = token[b:]
        score = self.scores.get(subtoken, self.unknown_score)
        return [Token(subtoken, b, len(token), score, len(subtoken))]


class MaxLRScoreTokenizer:
    def __init__(self, Dl=None, Dr=None,
                 preference_l=None, preference_r=None,
                 lrgraph=None, tokenizer_builder=None,
                 max_lscore_difference=0.3, max_lscore_diffratio=0.5, # Expansion L
                 ensurable_score_l=0.5, ensurable_score_lr_diff=0.3   # R overlap L
                ):

        # Normalize L-R graph to prob graph
        def norm(rdict):
            sum_ = sum(rdict.values())
            return {r:c/sum_ for r,c in rdict.items()}
        self.lrgraph = lrgraph if lrgraph else {}
        self.lrgraph_norm = {l:norm(rdict) for l,rdict in self.lrgraph.items()}

        # Expanding dictionary from lrgraph
        #self.Dl, self.Dr = tokenizer_builder(self.lrgraph) if tokenizer_builder else LRTokenizerBuilder()(self.lrgraph)
        self.Dl, self.Dr = tokenizer_builder(self.lrgraph) if tokenizer_builder else ({}, {})
        
        # Dictionary type check
        if not Dl: Dl = {}
        if not Dr: Dr = {}

        if not type(Dl) == dict:
            Dl = {l:1.0 for l in Dl}
        self.Dl.update(Dl)
        if not type(Dr) == dict:
            Dr = {r:1.0 for r in Dr}
        self.Dr.update(Dr)

        # Add preference words into dictionary
        self.Pl = preference_l if preference_l else {}
        self.Pr = preference_r if preference_r else {}

        for l in self.Pl:
            if not (l in self.Dl):
                self.Dl[l] = 1.0
        for r in self.Pr:
            if not (r in self.Dr):
                self.Dr[r] = 1.0

        self.lmax = max((len(w) for w in self.Dl)) if self.Dl else 0
        self.rmax = max((len(w) for w in self.Dr)) if self.Dr else 0
        self.base_tokenizer = MaxScoreTokenizer(scores=self.Dr)
        
        self.max_lscore_difference = max_lscore_difference
        self.max_lscore_diffratio = max_lscore_diffratio
        self.ensurable_score_l = ensurable_score_l
        self.ensurable_score_lr_diff = ensurable_score_lr_diff

    def __call__(self, sent, debug=True, flatten=True):
        return self.tokenize(sent, debug, flatten)

    def tokenize(self, sent, debug=False, flatten=True):
        sent_ = [self._tokenize(t, debug) for t in sent.split() if t]
        if flatten:
            sent_ = [word for words in sent_ for word in words]
        return sent_

    def _tokenize(self, t, debug=False):
        candidates = self._initialize(t)
        candidates_ = self._remove_l_subset(candidates)
        scores = self._score(candidates_)
        best = self._find_best(scores)
        
        if best:
            post = self._postprocessing(t, best)
        else:
            post = self._base_tokenizing_subword(t, 0)

        if not debug:
            post = [[(p[0], 'L'), (p[1], 'R')] for p in post]
            post = [w for p in post for w in p if w[0]]
        return post
    
    def _initialize(self, t):
        candidates = self._initialize_L(t)
        candidates = self._initialize_LR(t, candidates)
        return candidates

    def _initialize_L(self, t):
        n = len(t)
        candidates = []
        for b in range(n):
            for e in range(b+1, min(n, b+self.lmax)+1):
                l = t[b:e]
                if not (l in self.Dl):
                    continue
                candidates.append([l,     # 0
                                   b,     # 1                  
                                   e,     # 2
                                   e-b    # 3
                                  ])
        return candidates

    def _initialize_LR(self, t, candidates):
        n = len(t)
        expanded = []
        for (l, b, e, len_l) in candidates:
            for len_r in range(min(self.rmax, n-e)+1):
                if len_l == 1 and len_r == 0:
                    continue
                r = t[e:e+len_r]
                if r and not (r in self.Dr):
                    continue
                expanded.append([l,
                                 r,
                                 b,
                                 e,
                                 e + len_r,
                                 len_l,
                                 len_r,
                                 len_l + len_r,
                                ])
        return sorted(expanded, key=lambda x:x[4])
    
    def _remove_l_subset(self, candidates):    
        for c in candidates:
            c.append(self.Dl.get(c[0], 0))
            c.append(self.Dr.get(c[1], 0))
        candidates = sorted(candidates, key=lambda x:-x[-2])

        candidates_ = []
        while candidates:
            best = candidates.pop(0)
            b, e, lscore = best[2], best[3], best[-2]

            exist_longer = False
            for c in candidates:
                if c[2] > b or c[3] < e or not (c[2] < b or c[3] > e):
                    continue
                if ((lscore - c[-2]) < self.max_lscore_difference) or \
                    ((self.ensurable_score_l * 0.5 < lscore) and \
                        ((lscore+1e-5) / (c[-2]+1e-5) < self.max_lscore_diffratio)):
                    exist_longer = True
                    break

            if not exist_longer:
                candidates_.append(best)

        return candidates_

    def _score(self, candidates):
        from collections import defaultdict
        # With checking R is overlapped next L
        begin_to_words = defaultdict(lambda: [])
        for c in candidates:
            begin_to_words[c[2]].append(c)
        begin_to_words = dict(begin_to_words)

        scored = []

        candidates = sorted(candidates, key=lambda x:(-x[-2], -x[-1], x[2], -x[5]))
        while candidates:
            c = candidates.pop(0)
            l, r, p0, p1, p2, len_l, len_r, len_lr, score_l, score_r = c

            # Check whether R is overlapped next L
            if len_r:
                overlappped = False
                for b in range(p1, p2):
                    if overlappped:
                        break
                    for word in begin_to_words.get(b, []):
                        score_diff = word[-2] + self.Pl.get(word[0], 0) - score_r
                        if (self.ensurable_score_l <= word[-2]) or (score_diff > self.ensurable_score_lr_diff):
                            overlappped = True
                            break
                if overlappped:
                    continue

            total_score = (score_l * 2 if not r else score_l + score_r) + self.Pl.get(l, 0) + self.Pr.get(r, 0)
            c.append(total_score)
            scored.append(c)
        return scored

    def _find_best(self, scores):
        best = []
        sorted_ = sorted(scores, key=lambda x:-x[-1])
        while sorted_:
            best.append(sorted_.pop(0))
            (b, e) = (best[-1][2], best[-1][4])
            removals = [i for i, c in enumerate(sorted_) if b < c[4] and e > c[2]] # Overlap
            for idx in reversed(removals):
                del sorted_[idx]
        return sorted(best, key=lambda x:x[2])

    def _postprocessing(self, t, words):
        n = len(t)
        adds = []
        if words and words[0][2] > 0:
            adds += self._add_first_subword(t, words)
        if words and words[-1][3] < n:
            adds += self._add_last_subword(t, words, n)
        adds += self._add_inter_subwords(t, words)
        post = [w for w in words] + adds
        return sorted(post, key=lambda x:x[2])

    def _add_inter_subwords(self, t, words):
        adds = []        
        for i, base in enumerate(words[:-1]):
            if base[4] == words[i+1][2]:
                continue
            b = base[4]
            e = words[i+1][2]
            subword = t[b:e]
            adds += self._base_tokenizing_subword(subword, b)
        return adds

    def _add_last_subword(self, t, words, n):
        b = words[-1][3]
        subword = t[b:]
        return self._base_tokenizing_subword(subword, b)

    def _add_first_subword(self, t, words):    
        e = words[0][2]
        subword = t[0:e]
        return self._base_tokenizing_subword(subword, 0)

    def _base_tokenizing_subword(self, t, b):
        words = self.base_tokenizer.tokenize(t)
        words_ = []
        b_ = 0
        for w in words:
            n = len(w)
            # TODO: 여기를 바꿔야해
            if w in self.Dr:
                words_.append(['', w, b+b_, b+b_, b+n, 0, n, n, 0, self.base_tokenizer.scores[w]])
            else:
                words_.append([w, '', b+b_, b+n, b+n, n, 0, n, 0, 0])
        return words_
