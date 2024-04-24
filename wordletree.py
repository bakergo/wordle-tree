#!/usr/bin/env python3

import tqdm
import random
import math
import functools
import random

SCOREMAP={}
GUESSES=set()
ANSWERS=set()

with open('guesses.txt', 'r') as f:
    for line in f:
        GUESSES.add(line.lower().strip())
with open('answers.txt', 'r') as f:
    for line in f:
        ANSWERS.add(line.lower().strip())

GUESSES.update(ANSWERS)

def posmap(string:str):
    return {i:string[i] for i in range(len(string))}

# @functools.cache
def score(guess:str, against:str):
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


def bucket(guess:str, answers: set):
    return _bucket_small(guess, answers)

def _bucket_small(guess:str, answers: set):
    buckets = {}
    for answer in answers:
        wordscore = score(guess, answer)
        if wordscore not in buckets:
            buckets[wordscore] = set()
        buckets[wordscore].add(answer)
    if len(buckets) > 64:
        bucket_list = [(len(words),score,words) for score,words in buckets.items()]
        bucket_list.sort()
        bucket_list = [(score, words) for _, score, words in bucket_list]
    else:
        bucket_list = [(score, words) for score, words in buckets.items()]
    return bucket_list


def get_any_better_guess(guesses, answers: set, beat, max_depth=6, postfix="root"):
    """Returns a tree with the minimum total guesses required."""
    # Impossible benchmark, fail.
    if max_depth <= 0:
        return 1, None, None
    if len(answers) == 1:
        answer = next(iter(answers))
        return 1, answer, None
    if math.log(len(answers), 243) + 1 >= min(beat, max_depth):
        return 1, None, None
    if len(answers) > beat:
        return 1, None, None
    upper_bound = beat
    best_score = float('inf')
    best_guess = None
    best_tree = {}

    # Randomly select some percentage of guesses along with up to 40 answers and rank those only.
    guesses_in_question = []
    guesses_in_question.extend(answers)
    guesses_in_question.extend(random.sample(guesses, len(guesses)//10))
    # guesses_in_question = set(guesses_in_question)

    # For each guess, break the answers down into buckets by guess, then
    # look for the most promising guess - the one with the lowest maximum
    # bucket size.
    guessed = set()
    guess_order = []
    for guess in tqdm.tqdm(guesses_in_question, unit="guess", leave=False, postfix="bucketing", ncols=120):
        if guess in guessed:
            continue
        guessed.add(guess)
        distr = bucket(guess, answers)
        weight = sum((len(words)*math.log(len(words), 2) for wordscore,words in distr))
        guess_order.append((weight, guess, distr))
        if len(distr) >= len(answers):
            # Stop considering alternatives if the list is full. Because answers are ordered before
            # non-answer guesses, this will always find an optimal solution if it exists
            break
    answers_sorted = guess_order[:len(answers)]
    guess_order = sorted(guess_order[len(answers):])
    guess_order = answers_sorted + guess_order
    guess_order.sort()
    guess_order = guess_order[:50]
    optimal_for_distr = 0.
    guessed.clear()
    # guess_stack=random.sample(list(guesses), k=len(guesses))
    for (weight, guess, distr) in tqdm.tqdm(guess_order, unit="guess", leave=False, postfix=postfix, ncols=120):
        if upper_bound < len(answers):
            # Return if an optimal solution to bucket is found.
            break
        if guess in guessed:
            continue
        guessed.add(guess)
        guess_tree = {}
        guess_total = 1.
        answered = 0
        for (score, next_words) in tqdm.tqdm(distr,
                                             total=len(distr),
                                             unit="bucket",
                                             leave=False,
                                             postfix="%s; best: %s" % (guess, best_guess),
                                             ncols=120):
            next_guesses = guesses
            # Trim down the guess budget for the subcall based on the number of items in this
            # bucket. If each child takes on average upper_bound, we hit the budget.
            # * Remove the used budget (upper_bound - guess_total)
            # * subtract 1 for each other guess not covered (len(answers) - answered + next_words + 1)
            total_budget_for_kids = upper_bound - guess_total - len(answers) + answered + len(next_words) + 1
            if total_budget_for_kids > upper_bound:
                raise Exception("bound: %d < budget: %d; total: %d len: %d answered: %d distr: %d, next_words: %d" % (upper_bound, total_budget_for_kids, guess_total, len(answers), answered, len(distr), len(next_words)))
            # Use no more than max_depth - 1
            budget = total_budget_for_kids
            if score == 'GGGGG':
                next_guess_total, next_guess, tree = (0, guess, None)
            elif guess_total + len(next_words) > upper_bound:
                next_guess_total, next_guess, tree = (float('inf'), None, None)
            else:
                next_guess_total, next_guess, tree = get_any_better_guess(next_guesses, next_words, budget, max_depth=max_depth-1, postfix="%s (%d words)" % (score, len(next_words)))

            if next_guess is None:
                # This bucket is unsolveable in the budget and depth
                guess_total = float('inf')
                break
            answered += len(next_words)
            guess_total += next_guess_total
            if guess_total + len(answers) - answered > upper_bound:
                # Over budget.
                guess_total = float('inf')
                break
            if tree:
                guess_tree[score] = (next_guess, tree)
            else:
                guess_tree[score] = (next_guess)
        # TODO: Track guess_total separately from upper_bound. Use upper_bound - 1 for the next
        # guesses.
        if guess_total < best_score:
            # This guess beat the current best.
            upper_bound = guess_total - 1
            best_score = guess_total
            best_guess = guess
            best_tree = guess_tree
    return best_score, best_guess, best_tree


def solve_wordle():
    depth,guess,tree = get_any_better_guess(GUESSES, ANSWERS, beat=float('inf'))
    print("A solution exists for wordle in %d total guesses, with %s as the start." % (depth, guess))
    print("The guess tree follows:")
    print((guess, tree))
    print("A solution exists for wordle in %d total guesses, with %s as the start." % (depth, guess))


def main():
    # precompute_buckets()
    solve_wordle()

main()

