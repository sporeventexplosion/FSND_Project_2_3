#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


class Tournament():
    """An object-oriented representation of a single tournament.

    This approach reduces the overhead caused by re-connecting on every
    function call by storing the connection in an object."""

    def __init__(self, dbname="tournament"):
        """Connect to the database "dbname" (defaults to "tournament")"""
        self.db = psycopg2.connect("dbname=" + dbname)

    def close(self):
        """closes database stored in the self object"""
        self.db.close()

    def deleteMatches(self):
        """Remove all the match records from the database."""

        # Assigning self.db to db purely for convenience
        db = self.db
        cur = db.cursor()
        cur.execute("DELETE FROM matches")
        db.commit()

    def deletePlayers(self):
        """Remove all the player records from the database."""

        db = self.db
        cur = db.cursor()
        cur.execute("DELETE FROM players")
        db.commit()

    def countPlayers(self):
        """Returns the number of players currently registered."""

        db = self.db
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) as num FROM players")
        result = cur.fetchone()[0]

        return result

    def registerPlayer(self, name):
        """Adds a player to the tournament database.

        The database assigns a unique serial id number for the player.  (This
        should be handled by your SQL database schema, not in your Python
        code.)

        Args:
          name: the player's full name (need not be unique).
        """
        db = self.db
        cur = db.cursor()
        # The extra comma at the end is needed to force Python to treat (name)
        # as a tuple
        cur.execute("INSERT INTO players (name) VALUES (%s)", (name,))
        db.commit()

    def playerStandings(self):
        """Returns a list of the players and their win records, sorted by wins.

        The first entry in the list should be the player in first place, or a
        player tied for first place if there is currently a tie.

        Returns:
          A list of tuples, each of which contains (id, name, wins, matches):
            id: the player's unique id (assigned by the database)
            name: the player's full name (as registered)
            wins: the number of matches the player has won
            matches: the number of matches the player has played
        """
        db = self.db
        cur = db.cursor()
        cur.execute("SELECT * FROM standings")
        result = cur.fetchall()

        return result

    def reportMatch(self, winner, loser):
        """Records the outcome of a single match between two players.

        Args:
          winner:  the id number of the player who won
          loser:  the id number of the player who lost
        """

        db = self.db
        cur = db.cursor()
        q = "INSERT INTO matches (player1, player2, winner) VALUES (%s, %s, %s)"
        cur.execute(q, (winner, loser, winner))
        db.commit()


    def swissPairings(self):
        """Returns a list of pairs of players for the next round of a match.

        Assuming that there are an even number of players registered, each player
        appears exactly once in the pairings.  Each player is paired with another
        player with an equal or nearly-equal win record, that is, a player adjacent
        to him or her in the standings.

        Returns:
          A list of tuples, each of which contains (id1, name1, id2, name2)
            id1: the first player's unique id
            name1: the first player's name
            id2: the second player's unique id
            name2: the second player's name
        """

        db = self.db
        cur = db.cursor()
        cur.execute("SELECT * FROM swiss_pairings")
        result = cur.fetchall()

        return result
