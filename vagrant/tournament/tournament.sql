-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

-- Start with a blank table
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;

\c tournament

-- Players table
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name TEXT
);

-- Matches table
CREATE TABLE matches (
    player1 INTEGER REFERENCES players(id),
    player2 INTEGER REFERENCES players(id),
    winner INTEGER REFERENCES players(id),
    -- Re-matches are not allowed
    PRIMARY KEY (player1, player2)
);

-- Number of wins for a player
CREATE VIEW player_wins AS SELECT players.id, COUNT(matches.winner) AS num_won
FROM players LEFT JOIN matches ON players.id = matches.winner
GROUP BY players.id ORDER BY num_won DESC;

-- Number of matches played by a player
CREATE VIEW player_matches AS SELECT players.id, COUNT(matches.*) AS num_played
FROM players LEFT JOIN matches ON matches.player1 = players.id
OR matches.player2 = players.id GROUP BY players.id
ORDER BY num_played DESC;

-- Player's current standings
CREATE VIEW standings AS SELECT players.id, players.name, player_wins.num_won,
player_matches.num_played FROM players JOIN player_wins ON
player_wins.id = players.id JOIN player_matches
ON player_matches.id = players.id ORDER BY player_wins.num_won;

-- Simple numbered standings view used in the pairing process so it does not
-- have to be repeated in swiss-pairing

CREATE VIEW numbered_standings AS SELECT *, ROW_NUMBER() OVER() as num FROM standings;


-- Result for swiss-style pairing done in the database.
CREATE VIEW swiss_pairings AS SELECT a.id AS id1, a.name AS name1, b.id AS id2,
b.name as name2 FROM numbered_standings AS a, numbered_standings AS b WHERE
a.num = b.num - 1 AND a.num % 2 = 1 ORDER BY a.num_won DESC;
