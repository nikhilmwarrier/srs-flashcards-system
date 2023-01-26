#!/bin/python

# spaced repetition system that I'm coding as a way of procrastination. Please send help.

# using the SM2+ algorithm (http://www.blueraja.com/blog/477/a-better-spaced-repetition-learning-algorithm-sm2)

import os
import sys
import sqlite3

import colorama as col

from time import strftime
from datetime import date
from random import randint
from config.definitions import ROOT_DIR as ROOT_DIR_PRESET, BASE_DIR


ROOT_DIR = ROOT_DIR_PRESET

try:
    if sys.argv[1]:
        ROOT_DIR = os.path.join(BASE_DIR, sys.argv[1]) 
        try:
            os.makedirs(ROOT_DIR)
        except FileExistsError:
            pass
except IndexError:
    ROOT_DIR = ROOT_DIR_PRESET

PERFORMANCE_THRESHOLD = 0.6

col.init(autoreset=True)    # Initialize Colorama

con = sqlite3.connect(os.path.join(ROOT_DIR, "cards_data.db"))
cur = con.cursor()

# cur.execute("DROP TABLE cards")
# con.commit()

try:
    os.makedirs(os.path.join(ROOT_DIR, "new_cards"))
    os.makedirs(os.path.join(ROOT_DIR, "./saved_cards"))
except FileExistsError:
    pass

cur.execute("CREATE TABLE IF NOT EXISTS cards(filename, performanceRating, difficulty, daysBetweenReviews, dateLastReviewed, percentOverdue, difficultyWeight, wasCorrectLastTime)")

# Helper Functions


def clamp(_min, _max, val):
    return max(_min, min(val, _max))


def calculateDaysFrom(iso_date):
    return (date.today() - date.fromisoformat(iso_date)).days


def int_input(prompt):
    try:
        return int(input(prompt))
    except ValueError:
        print(col.Style.BRIGHT + col.Fore.RED + "Invalid number. Try again.")
        return int_input(prompt)

# Formula Helper Functions


def calculateDifficulty(currentDifficulty, percentOverdue, performanceRating):
    return (currentDifficulty + percentOverdue * (1/17) * (8 - (9 * performanceRating)))


def calculateDifficultyWeight(difficulty) -> float:
    return 3 - (1.7 * difficulty)


def calculateDaysBetweenReviews(currentDaysBetweenReviews, percentOverdue, difficultyWeight, difficulty, isCorrect):
    if isCorrect:
        return (currentDaysBetweenReviews * (1 + (difficultyWeight-1) * percentOverdue * (randint(95, 105)/100)))
    else:
        return 1 / (1 + (3 * difficulty))


def calculatePercentOverdue(dateLastReviewed, daysBetweenReviews, isCorrect):
    if isCorrect:
        return min(2, calculateDaysFrom(dateLastReviewed)/daysBetweenReviews)
    else:
        return 1

# Main Logic


def addNewCards(cards_list):
    print(col.Style.DIM + col.Fore.GREEN +
          f"{ len(cards_list) } new card(s) detected!")

    cards_list_with_difficulty = []

    for card in cards_list:
        _difficulty = open(os.path.join(ROOT_DIR, "new_cards", card)).read().split('\n')[0]
        try:
            float_difficulty = int(_difficulty) / 10
            float_difficulty = clamp(0.0, 1.0, float_difficulty)
            cards_list_with_difficulty.append((card, float_difficulty))
        except ValueError:
            print(col.Style.BRIGHT + col.Fore.RED +
                  f"Error: Couldn't read difficulty of { card }. Skipping...")

    cards_list_formatted = [
        (filename, 0, difficulty, 1, strftime("%Y-%m-%d"), 1, calculateDifficultyWeight(difficulty), 0) for (filename, difficulty) in cards_list_with_difficulty]

    cur.executemany(
        "INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?)", cards_list_formatted)
    con.commit()

    for card in cards_list:
        os.rename(os.path.join(ROOT_DIR, f"new_cards/{card}"), os.path.join(ROOT_DIR, f"saved_cards/{card}"))


def updateCardDetails(performanceRatings):
    cards = [c[0]
             for c in cur.execute("SELECT filename FROM cards").fetchall()]
    for card in cards:
        row_values = cur.execute(
            "SELECT * FROM cards WHERE filename = ?", (card,)).fetchone()
        currPerformaceRating = row_values[1]
        currDifficulty = row_values[2]
        currDaysBetweenReviews = row_values[3]
        currDateLastReviewed = row_values[4]
        currPercentOverdue = row_values[5]
        currDifficultyWeight = row_values[6]
        wasCorrectLastTime = row_values[7]

        if performanceRatings and performanceRatings.get(card, False):
            _isCorrect = 1 if (
                performanceRatings[card] >= PERFORMANCE_THRESHOLD) else 0
            newPercentOverdue = calculatePercentOverdue(
                currDateLastReviewed, currDaysBetweenReviews, _isCorrect)
            newDaysBetweenReviews = calculateDaysBetweenReviews(
                currDaysBetweenReviews, newPercentOverdue, currDifficultyWeight, currDifficulty, _isCorrect)
            newDifficulty = calculateDifficulty(
                currDifficulty, newPercentOverdue, performanceRatings[card])
            newDifficultyWeight = calculateDifficultyWeight(newDifficulty)
            newDateLastReviewed = date.isoformat(date.today())

            values = (
                performanceRatings[card],
                newDifficulty,
                newDaysBetweenReviews,
                newDateLastReviewed,
                newPercentOverdue,
                newDifficultyWeight,
                _isCorrect,
                card
            )
            cur.execute("""UPDATE cards
                                SET performanceRating = ?,
                                difficulty = ?,
                                daysBetweenReviews = ?,
                                dateLastReviewed = ?,
                                percentOverdue = ?,
                                difficultyWeight = ?,
                                wasCorrectLastTime = ?
                            WHERE filename = ?""", values)
        else:
            _isCorrect = wasCorrectLastTime

            newPercentOverdue = calculatePercentOverdue(
                currDateLastReviewed, currDaysBetweenReviews, _isCorrect)

            values = (
                newPercentOverdue,
                card
            )

            cur.execute(
                "UPDATE cards SET percentOverdue = ? WHERE filename = ?", values)

        con.commit()


new_cards = os.listdir(os.path.join(ROOT_DIR, 'new_cards'))

if len(new_cards) != 0:
    addNewCards(new_cards)


def cardsLoop():
    cards = cur.execute(
        "SELECT * FROM cards WHERE percentOverdue >= 0.9 ORDER BY percentOverdue DESC").fetchall()

    performanceRatings_dict = {}

    for card in cards:
        (card_content := open(os.path.join(ROOT_DIR,
         'saved_cards', card[0])).read().split('\n'))
        qn = card_content[1]
        ans = card_content[2]
        print(col.Style.DIM +
              f"\n\n(Card: {card[0]}) (Press <ENTER> to reveal answer)\n")
        print(col.Style.BRIGHT + col.Fore.BLUE + qn)
        input("> Enter what you recall: ")
        print(col.Style.BRIGHT + col.Fore.LIGHTGREEN_EX + ans)
        performanceRating = int_input(
            "> How well did you perform? <0-5>: ") / 5
        performanceRating = clamp(0.0, 1.0, performanceRating)
        print("Your performance: " + col.Style.BRIGHT + ((col.Fore.RED + str(performanceRating * 100) + '%')
              if (performanceRating < 0.6) else (col.Fore.GREEN + str(performanceRating * 100) + '%')))

        performanceRatings_dict[card[0]] = performanceRating

    if performanceRatings_dict:
        updateCardDetails(performanceRatings_dict)
    else:
        updateCardDetails(False)
    print(col.Style.BRIGHT + col.Fore.CYAN + "\n\nAll done for today!")


cardsLoop()
