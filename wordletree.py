#!/usr/bin/env python3

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

def main():
    easy_hist, easy_beaten_by = make_hist(False)
    hard_hist, hard_beaten_by = make_hist(False)
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

main()

