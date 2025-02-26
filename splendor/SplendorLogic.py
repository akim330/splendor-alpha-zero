'''
Author: Eric P. Nichols
Date: Feb 8, 2008.
Board class.
Board data:
  1=white, -1=black, 0=empty
  first dim is column , 2nd is row:
     pieces[1][7] is the square in column 2,
     at the opposite end of the board in row 8.
Squares are stored and manipulated as (x,y) tuples.
x is the column, y is the row.
'''

import numpy as np
import random
import queue



class Card():
    def __init__(self, level, color, pv, w, u, g, r, k):
        self.level = level
        self.color = color
        self.pv = pv
        self.w = w
        self.u = u
        self.g = g
        self.r = r
        self.k = k

    def __repr__(self):
        return f"Card(level={self.level}, color={self.color}, PV={self.pv}, {self.w}W, {self.u}U, {self.g}G, {self.r}R, {self.k}K"

class Noble():
    def __init__(self, id, pv, w, u, g, r, k):
        self.id = id
        self.pv = pv

        self.w = w
        self.u = u
        self.g = g
        self.r = r
        self.k = k

    def __repr__(self):
        return f"Noble(id={self.id}, PV={self.pv}, {self.w}W, {self.u}U, {self.g}G, {self.r}R, {self.k}K"


row_count = 4


class Board():
    def __init__(self, n):
        "Set up initial board configuration."
        # Randomize deck
        n_level_1_cards = len(level_1_cards)
        n_level_2_cards = len(level_2_cards)
        n_level_3_cards = len(level_3_cards)

        n_cards = n_level_1_cards + n_level_2_cards + n_level_3_cards

        self.deck1 = queue.Queue()
        self.deck2 = queue.Queue()
        self.deck3 = queue.Queue()

        id_list1 = list(range(40))
        id_list2 = list(range(40, 70))
        id_list3 = list(range(70, 90))

        random.shuffle(id_list1)
        random.shuffle(id_list2)
        random.shuffle(id_list3)

        for card in id_list1:
            self.deck1.put(card)
        for card in id_list2:
            self.deck2.put(card)
        for card in id_list3:
            self.deck3.put(card)

        self.board = np.zeros(n_cards)

        self.reserved_level_1 = np.zeros(n_level_1_cards)
        self.reserved_level_2 = np.zeros(n_level_2_cards)
        self.reserved_level_3 = np.zeros(n_level_3_cards)

        # Draw 4 cards for each level
        for _ in range(row_count):
            current_card_id = self.deck1.get()
            self.board[current_card_id] = 1

            current_card_id = self.deck2.get()
            self.board[current_card_id] = 1

            current_card_id = self.deck3.get()
            self.board[current_card_id] = 1

        # Pick 3 nobles
        self.nobles = random.sample(nobles_list, 3)

        # Player coins
        self.p1_coins = {
            'k': 0,
            'u': 0,
            'g': 0,
            'r': 0,
            'w': 0,
            'y': 0
        }

        self.p2_coins = {
            'k': 0,
            'u': 0,
            'g': 0,
            'r': 0,
            'w': 0,
            'y': 0
        }

    # add [][] indexer syntax to the Board
    def __getitem__(self, index): 
        return self.pieces[index]

    def countDiff(self, color):
        """Counts the # pieces of the given color
        (1 for white, -1 for black, 0 for empty spaces)"""
        count = 0
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y]==color:
                    count += 1
                if self[x][y]==-color:
                    count -= 1
        return count

    def get_legal_moves(self, color):
        """Returns all the legal moves for the given color.
        (1 for white, -1 for black
        """
        moves = set()  # stores the legal moves.

        # Get all the squares with pieces of the given color.
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y]==color:
                    newmoves = self.get_moves_for_square((x,y))
                    moves.update(newmoves)
        return list(moves)

    def has_legal_moves(self, color):
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y]==color:
                    newmoves = self.get_moves_for_square((x,y))
                    if len(newmoves)>0:
                        return True
        return False

    def get_moves_for_square(self, square):
        """Returns all the legal moves that use the given square as a base.
        That is, if the given square is (3,4) and it contains a black piece,
        and (3,5) and (3,6) contain white pieces, and (3,7) is empty, one
        of the returned moves is (3,7) because everything from there to (3,4)
        is flipped.
        """
        (x,y) = square

        # determine the color of the piece.
        color = self[x][y]

        # skip empty source squares.
        if color==0:
            return None

        # search all possible directions.
        moves = []
        for direction in self.__directions:
            move = self._discover_move(square, direction)
            if move:
                # print(square,move,direction)
                moves.append(move)

        # return the generated move list
        return moves

    def execute_move(self, move, color):
        """Perform the given move on the board; flips pieces as necessary.
        color gives the color pf the piece to play (1=white,-1=black)
        """

        #Much like move generation, start at the new piece's square and
        #follow it on all 8 directions to look for a piece allowing flipping.

        # Add the piece to the empty square.
        # print(move)
        flips = [flip for direction in self.__directions
                      for flip in self._get_flips(move, direction, color)]
        assert len(list(flips))>0
        for x, y in flips:
            #print(self[x][y],color)
            self[x][y] = color

    def _discover_move(self, origin, direction):
        """ Returns the endpoint for a legal move, starting at the given origin,
        moving by the given increment."""
        x, y = origin
        color = self[x][y]
        flips = []

        for x, y in Board._increment_move(origin, direction, self.n):
            if self[x][y] == 0:
                if flips:
                    # print("Found", x,y)
                    return (x, y)
                else:
                    return None
            elif self[x][y] == color:
                return None
            elif self[x][y] == -color:
                # print("Flip",x,y)
                flips.append((x, y))

    def _get_flips(self, origin, direction, color):
        """ Gets the list of flips for a vertex and direction to use with the
        execute_move function """
        #initialize variables
        flips = [origin]

        for x, y in Board._increment_move(origin, direction, self.n):
            #print(x,y)
            if self[x][y] == 0:
                return []
            if self[x][y] == -color:
                flips.append((x, y))
            elif self[x][y] == color and len(flips) > 0:
                #print(flips)
                return flips

        return []

    @staticmethod
    def _increment_move(move, direction, n):
        # print(move)
        """ Generator expression for incrementing moves """
        move = list(map(sum, zip(move, direction)))
        #move = (move[0]+direction[0], move[1]+direction[1])
        while all(map(lambda x: 0 <= x < n, move)): 
        #while 0<=move[0] and move[0]<n and 0<=move[1] and move[1]<n:
            yield move
            move=list(map(sum,zip(move,direction)))
            #move = (move[0]+direction[0],move[1]+direction[1])

