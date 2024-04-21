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


def bucket(guess, answers: set):
    if not BUCKETS:
        precompute_buckets()
    buckets = BUCKETS[guess]
    aset = answers
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


def get_any_better_guess(guesses, answers: set, beat, max_depth=6, postfix="root"):
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
    guess_order.sort()
    guess_order = guess_order[:len(guesses)//100]

    # guess_stack=random.sample(list(guesses), k=len(guesses))
    for (weight, guess, distr) in tqdm.tqdm(guess_order, unit="guess", leave=False, postfix=postfix, ncols=120):
        guess_tree = {}
        guess_total = 0.
        guessed_count = 0
        len_distr = len(distr)
        for (score, next_words) in tqdm.tqdm(distr.items(),
                                             total=len(distr),
                                             unit="bucket",
                                             leave=False,
                                             postfix=guess,
                                             ncols=120):
            next_guesses = guesses
            # Trim down the guess budget for the subcall based on the number of items in this
            # bucket.
            # If each child takes on average upper_bound, we hit the budget.
            total_budget_for_kids = (upper_bound * len_distr
                                     # There are len_distr - 1 other buckets. They can take at minimum 1.
                                     # Other guesses are included in guess_total
                                     -(len_distr - guessed_count - 1)
                                     # guess_total budget has already been used.
                                     -guess_total)
            # Use no more than max_depth - 1
            budget = min(total_budget_for_kids, max_depth - 1)
            if score == 'GGGGG':
                next_guess_average, next_guess, tree = (0, guess, None)
            else:
                next_guess_average, next_guess, tree = get_any_better_guess(next_guesses, next_words, budget, max_depth=max_depth-1, postfix=score)
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
        if upper_bound <= (1 + (len_distr-1)/len_distr) and best_guess:
            # Optimal
            break
    return upper_bound + 1, best_guess, best_tree


def solve_wordle():
    depth,guess,tree = get_any_better_guess(GUESSES, ANSWERS, beat=7.)
    print("A solution exists for wordle in %f guesses, with %s as the start." % (depth, guess))
    print("The guess tree follows:")
    print(tree)
    print("A solution exists for wordle in %f guesses, with %s as the start." % (depth, guess))


def main():
    solve_wordle()

main()

