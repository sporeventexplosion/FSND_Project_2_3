#!/usr/bin/env python
#
# Test cases for tournament.py

import tournament


def testOpenClose():
    t = tournament.Tournament()
    t.close()

    print "1. The database can be opened and closed"


def testDeleteMatches():
    t = tournament.Tournament()

    t.deleteMatches()

    t.close()
    print "2. Old matches can be deleted."


def testDelete():
    t = tournament.Tournament()

    t.deleteMatches()
    t.deletePlayers()

    t.close()
    print "3. Player records can be deleted."


def testCount():
    t = tournament.Tournament()

    t.deleteMatches()
    t.deletePlayers()
    c = t.countPlayers()
    if c == '0':
        raise TypeError(
            "countPlayers() should return numeric zero, not string '0'.")
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")

    t.close()
    print "4. After deleting, countPlayers() returns zero."


def testRegister():
    t = tournament.Tournament()

    t.deleteMatches()
    t.deletePlayers()
    t.registerPlayer("Chandra Nalaar")
    c = t.countPlayers()
    if c != 1:
        raise ValueError(
            "After one player registers, countPlayers() should be 1.")

    t.close()
    print "5. After registering a player, countPlayers() returns 1."


def testRegisterCountDelete():
    t = tournament.Tournament()

    t.deleteMatches()
    t.deletePlayers()
    t.registerPlayer("Markov Chaney")
    t.registerPlayer("Joe Malik")
    t.registerPlayer("Mao Tsu-hsi")
    t.registerPlayer("Atlanta Hope")
    c = t.countPlayers()
    if c != 4:
        raise ValueError(
            "After registering four players, countPlayers should be 4.")
    t.deletePlayers()
    c = t.countPlayers()
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")

    t.close()
    print "6. Players can be registered and deleted."


def testStandingsBeforeMatches():
    t = tournament.Tournament()

    t.deleteMatches()
    t.deletePlayers()
    t.registerPlayer("Melpomene Murray")
    t.registerPlayer("Randy Schwartz")
    standings = t.playerStandings()
    if len(standings) < 2:
        raise ValueError("Players should appear in playerStandings even before"
                         " they have played any matches.")
    elif len(standings) > 2:
        raise ValueError("Only registered players should appear in standings.")
    if len(standings[0]) != 4:
        raise ValueError("Each playerStandings row should have four columns.")
    [(id1, name1, wins1, matches1), (id2, name2, wins2, matches2)] = standings
    if matches1 != 0 or matches2 != 0 or wins1 != 0 or wins2 != 0:
        raise ValueError(
            "Newly registered players should have no matches or wins.")
    if set([name1, name2]) != set(["Melpomene Murray", "Randy Schwartz"]):
        raise ValueError("Registered players' names should appear in "
                         "standings, even if they have no matches played.")

    t.close()
    print "7. Newly registered players appear \
in the standings with no matches."


def testReportMatches():
    t = tournament.Tournament()

    t.deleteMatches()
    t.deletePlayers()
    t.registerPlayer("Bruno Walton")
    t.registerPlayer("Boots O'Neal")
    t.registerPlayer("Cathy Burton")
    t.registerPlayer("Diane Grant")
    standings = t.playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    t.reportMatch(id1, id2)
    t.reportMatch(id3, id4)
    standings = t.playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2, id4) and w != 0:

            raise ValueError(
                    "Each match loser should have zero wins recorded.")

    t.close()
    print "8. After a match, players have updated standings."


def testPairings():
    t = tournament.Tournament()

    t.deleteMatches()
    t.deletePlayers()
    t.registerPlayer("Twilight Sparkle")
    t.registerPlayer("Fluttershy")
    t.registerPlayer("Applejack")
    t.registerPlayer("Pinkie Pie")
    standings = t.playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    t.reportMatch(id1, id2)
    t.reportMatch(id3, id4)
    pairings = t.swissPairings()
    if len(pairings) != 2:
        raise ValueError(
            "For four players, swissPairings should return two pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings
    correct_pairs = set([frozenset([id1, id3]), frozenset([id2, id4])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])
    if correct_pairs != actual_pairs:
        raise ValueError(
            "After one match, players with one win should be paired.")

    t.close()
    print "9. After one match, players with one win are paired."


if __name__ == '__main__':
    testDeleteMatches()
    testDelete()
    testCount()
    testRegister()
    testRegisterCountDelete()
    testStandingsBeforeMatches()
    testReportMatches()
    testPairings()
    print "Success!  All tests pass!"
