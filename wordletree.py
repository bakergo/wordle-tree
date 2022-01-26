#!/usr/bin/env python3

import tqdm
import random
import math

GUESSES=set()
ANSWERS=set()

with open('guesses.txt', 'r') as f:
    for line in f:
        GUESSES.add(line.lower().strip())
with open('answers.txt', 'r') as f:
    for line in f:
        ANSWERS.add(line.lower().strip())

GUESSES.update(ANSWERS)

def posmap(string):
    return {i:string[i] for i in range(len(string))}

def score(guess, against):
    '''Return a tuple of 5 integers representing the score of this word against the list'''
    r = [0] * 5
    guessletters = posmap(guess)
    againstletters = posmap(against)

    for k,v in guessletters.copy().items():
        if v == againstletters[k]:
            r[k] = 2
            del againstletters[k]
            del guessletters[k]

    for k,v in guessletters.items():
        for kb, vb in againstletters.items():
            if v == vb:
                del againstletters[kb]
                r[k] = 1
                break

    return tuple(r)


BUCKETS = {}
def precompute_buckets():
    for guess in tqdm.tqdm(GUESSES, unit="guess", postfix="pre-bucketing", leave=False, ncols=120, mininterval=1):
        BUCKETS[guess] = _bucket(guess, ANSWERS)


def bucket(guess, answers):
    if not BUCKETS:
        precompute_buckets()
    buckets = BUCKETS[guess]
    aset = set(answers)
    ret = {}
    for s, w in buckets.items():
        r = w & aset
        if r:
            ret[s] = r
    return ret


def _bucket(guess, answers):
    buckets = {}
    for word in answers:
        wordscore = score(guess, word)
        if wordscore in buckets:
            buckets[wordscore].add(word)
        else:
            buckets[wordscore] = set([word])
    return buckets


def filter_words(wordscore, guess, words):
    return [word for word in words if score(guess, word) == wordscore]

def get_best_guess(guesses, answers, hard_mode, beat, top_level=False, position=0, postfix=""):
    # Only one answer exists. Guess it
    if len(answers) == 1:
        answer = next(iter(answers))
        return 1, answer, {answer:None}
    # Beat is too small; we can't get it.
    if beat < math.ceil(math.log(len(answers), 243)) + 1:
        return beat+1, None, None
    best_guess_depth = beat
    best_guess = None
    best_tree = {}

    t=tqdm.tqdm(total=len(guesses), position=position, unit="guess", leave=False, postfix=postfix, ncols=120, mininterval=1)
    guess_order = []
    for guess in guesses:
        distr = bucket(guess, answers)
        weight = max((len(words) for wordscore,words in distr.items()))
        guess_order.append((weight, guess, distr))
    guess_order.sort(reverse=True)

    # guess_stack=random.sample(list(guesses), k=len(guesses))
    while guess_order:
        if best_guess_depth <= math.ceil(math.log(len(answers), 243)) and best_guess:
            # Theoretically impossible to beat this guess.
            break
        weight, guess, distr = guess_order.pop()
        t.update(n=1)
        guess_tree = {}
        guess_depth = float('-inf')
        for score, next_words in distr.items():
            if hard_mode:
                next_guesses = filter_words(score, guess, guesses)
            else:
                next_guesses = guesses
            depth, next_guess, tree = get_best_guess(next_guesses, next_words, hard_mode, best_guess_depth-1, position=position+1, postfix=guess)
            if next_guess is None:
                # Did not solve it.
                guess_depth = beat
                break
            if depth > guess_depth:
                guess_depth = depth
            if guess_depth >= best_guess_depth:
                break
            guess_tree[score] = (next_guess, tree)
        if guess_depth < best_guess_depth:
            best_guess_depth = guess_depth
            best_guess = guess
            best_tree = guess_tree
    return best_guess_depth + 1, best_guess, best_tree


def next_guess(guesses, answers):
    guessmin = {}
    for word in guesses:
        wordscores = {}

        for word2 in answers:
            wordscore = score(word, word2)
            if wordscore in wordscores:
                wordscores[wordscore] += [word2]
            else:
                wordscores[wordscore] = [word2]
            # print('%s : %s -> %s'% (word, word2, wordscore))
        maxv = max((tuple((len(x), 1 if word in ANSWERS else 0)) for x in wordscores.values()))
        guessmin[word] = maxv
    minimum = min(guessmin.values())
    for k,v in guessmin.items():
        if v == minimum:
            # print('%s is a good choice (score: %d)' % (k, v))
            return k

def guess_word_path(answer, hard_mode=False):
    valid_guesses = GUESSES
    valid_answers = ANSWERS
    # hard code it to save time.
    guess = 'aesir'
    # guess = next_guess(valid_guesses, valid_answers)
    guesses = 1
    while True:
        next_score = score(guess, answer)
        print("Guess %d: %s %s" % (guesses, guess, next_score))
        if next_score == (2,2,2,2,2):
            print("%s is the word. Got it in %d" % (guess, guesses))
            return guesses
        elif guesses >= 6:
            print("Couldn't get it sadge")
            return -1
        guesses += 1
        valid_answers = [word for word in valid_answers if score(guess, word) == next_score]
        if hard_mode:
            valid_guesses = [word for word in valid_guesses if score(guess, word) == next_score]
        if len(valid_answers) == 1:
            guess = valid_answers[0]
        else:
            guess = next_guess(valid_guesses, valid_answers)


def make_hist(hard_mode=False):
    beaten_by = set()
    hist = dict()
    for x in range(-1,7):
        hist[x] = 0
    for word in ANSWERS:
        guesses = guess_word_path(word, hard_mode=hard_mode)
        hist[guesses] += 1
        if guesses < 0:
            beaten_by.add(word)
    return hist, beaten_by


def print_hist(hist, hard_mode=False):
    print("%s mode histogram" % ("Hard" if hard_mode else "Easy"))
    for k in range(-1, 7):
        if k in hist:
            print("%-4s: %d" % ("fail" if k==-1 else str(k), hist[k]))


def solve_wordle():
    depth,guess,tree = get_best_guess(GUESSES, ANSWERS, hard_mode=False, beat=5, top_level=True)
    print("A solution exists for wordle in %d guesses, with %s as the start." % (depth, guess))
    print("The guess tree follows:")
    print(tree)
    print("A solution exists for wordle in %d guesses, with %s as the start." % (depth, guess))


def do_histograms():
    easy_hist, easy_beaten_by = make_hist(False)
    hard_hist, hard_beaten_by = make_hist(True)
    if easy_beaten_by:
        print("Beaten by these words on easy:")
        for word in easy_beaten_by:
            print(word)
    print_hist(easy_hist, hard_mode=False)
    if hard_beaten_by:
        print("Beaten by these words on hard:")
        for word in hard_beaten_by:
            print(word)
    print_hist(hard_hist, hard_mode=True)
    print("fin")

def main():
    # do_histograms()
    solve_wordle()

main()

