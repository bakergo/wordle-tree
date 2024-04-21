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
    r = ['.'] * 5
    guessletters = posmap(guess)
    againstletters = posmap(against)

    for k,v in guessletters.copy().items():
        if v == againstletters[k]:
            r[k] = 'G'
            del againstletters[k]
            del guessletters[k]

    for k,v in guessletters.items():
        for kb, vb in againstletters.items():
            if v == vb:
                del againstletters[kb]
                r[k] = 'y'
                break

    return ''.join(r)


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

def get_any_better_guess(guesses, answers, beat, max_depth=6, position=0, postfix="root"):
    """Returns a tree with the minimum total guesses required."""
    # Only one answer exists. Guess it
    if len(answers) == 1:
        answer = next(iter(answers))
        return 1, answer, None
    # Impossible benchmark, fail.
    if math.log(len(answers), 243) + 1 >= beat:
        return 1, None, None
    if max_depth <= 0:
        return 1, None, None
    upper_bound = beat-1
    best_guess = None
    best_tree = {}

    # For each guess, break the answers down into buckets by guess, then
    # look for the most promising guess - the one with the lowest maximum
    # bucket size.
    guess_order = []
    for guess in guesses:
        distr = bucket(guess, answers)
        weight = sum((len(words)*math.log(len(words), 2) for wordscore,words in distr.items()))
        guess_order.append((weight, guess, distr))
    guess_order.sort(reverse=True)
    guess_order = guess_order[-len(guesses)//100:]
    t=tqdm.tqdm(total=len(guess_order), position=position, unit="bucket", leave=False, postfix=postfix, ncols=120)

    # guess_stack=random.sample(list(guesses), k=len(guesses))
    while guess_order:
        weight, guess, distr = guess_order.pop()
        t.update(n=1)
        guess_tree = {}
        guess_total = 0.
        guessed_count = 0
        len_distr = len(distr)
        t2=tqdm.tqdm(total=len(distr), position=position+1, unit="guess", leave=False, postfix=guess, ncols=120)
        for score, next_words in distr.items():
            t2.update(n=1)
            next_guesses = guesses

            # Trim down the guess budget for the subcall based on the number of items in this
            # bucket.
            # If each child takes on average upper_bound, we hit the budget.
            total_budget_for_kids = upper_bound * len_distr
            # There are len_distr - 1 other buckets. They can take at minimum 1.
            # Other guesses are included in guess_total
            total_budget_for_kids -= len_distr - guessed_count - 1
            # guess_total budget has already been used.
            total_budget_for_kids -= guess_total
            # Use no more than max_depth - 1
            budget = min(total_budget_for_kids, max_depth - 1)
            next_guess_average, next_guess, tree = get_any_better_guess(next_guesses, next_words, budget, max_depth=max_depth-1, position=position+2, postfix=score)
            guessed_count += 1
            if next_guess is None:
                # This bucket is unsolveable in the budget and depth
                guess_total = 200000000
                break
            # Over budget.
            guess_total += next_guess_average
            if float(guess_total) / len_distr > upper_bound:
                guess_total = 200000000
                break
            guess_tree[score] = (next_guess, tree)
        if float(guess_total) / len_distr <= upper_bound:
            # This guess beat the current best.
            upper_bound = float(guess_total) / len_distr
            best_guess = guess
            best_tree = guess_tree
        if upper_bound <= 1 and best_guess:
            # Optimal
            break
    return upper_bound + 1, best_guess, best_tree


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
    depth,guess,tree = get_any_better_guess(GUESSES, ANSWERS, beat=7.)
    print("A solution exists for wordle in %f guesses, with %s as the start." % (depth, guess))
    print("The guess tree follows:")
    print(tree)
    print("A solution exists for wordle in %f guesses, with %s as the start." % (depth, guess))


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
    # any_wordle()

main()

