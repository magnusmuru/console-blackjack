"""Simple game of blackjack."""
from textwrap import dedent

import requests


class Card:
    """Simple dataclass for holding card information."""

    def __init__(self, value: str, suit: str, code: str):
        """"Initialize new card class."""
        self.value = value
        self.suit = suit
        self.code = code

    def __repr__(self):
        """"Return card model."""
        return self.code


class Hand:
    """Simple class for holding hand information."""

    def __init__(self):
        """"Initialize new card hand."""
        self.cards = []
        self.score = 0

    def add_card(self, card: Card):
        """"Add card to hand and calculate new hand value."""
        self.cards.append(card)
        new_score = 0
        has_aces = False
        for i in self.cards:
            if i.value in ['2', '3', '4', '5', '6', '7', '8', '9', '10']:
                new_score += int(i.value)
            if i.value in ['JACK', 'QUEEN', 'KING']:
                new_score += 10
            if i.value == 'ACE':
                new_score += 11
                has_aces = True
        if has_aces and new_score > 21:
            for i in self.cards:
                if i.value == 'ACE':
                    new_score -= 10
                if new_score <= 21:
                    break
        self.score = new_score


class Deck:
    """Deck of cards. Provided via api over the network."""

    def __init__(self, shuffle=False):
        """
        Tell api to create a new deck.

        :param shuffle: if shuffle option is true, make new shuffled deck.
        """
        if shuffle:
            self.deck = requests.get("https://deckofcardsapi.com/api/deck/new/shuffle").json()["deck_id"]
            self.is_shuffled = True
        else:
            self.deck = requests.get("https://deckofcardsapi.com/api/deck/new").json()["deck_id"]
            self.is_shuffled = False

    def shuffle(self):
        """Shuffle the deck."""
        requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/shuffle")
        self.is_shuffled = True

    def draw(self) -> Card:
        """
        Draw card from the deck.

        :return: card instance.
        """
        drawn_card = requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/draw").json()
        return Card(drawn_card["cards"][0]["value"], drawn_card["cards"][0]["suit"], drawn_card["cards"][0]["code"])


class BlackjackController:
    """Blackjack controller. For controlling the game and data flow between view and database."""

    def __init__(self, deck: Deck, view: 'BlackjackView'):
        """
        Start new blackjack game.

        :param deck: deck to draw cards from.
        :param view: view to communicate with.
        """
        if deck.is_shuffled is False:
            deck.shuffle()
        self.deck = deck
        self.view = view
        self.player = Hand()
        self.dealer = Hand()
        self.state = {"dealer": self.dealer, "player": self.player}

        for i in range(2):
            self.player.add_card(self.deck.draw())
            self.dealer.add_card(self.deck.draw())

        self.instant_win()
        if self.player.score < 21:
            self.player_plays()
        if self.player.score < 21:
            self.dealer_plays()

    def instant_win(self):
        """"Check for instant 21 point win."""
        if self.player.score == 21:
            self.view.player_won(self.state)

    def dealer_plays(self):
        """Model of dealer playing blackjack."""
        while self.dealer.score < 21 and self.dealer.score < self.player.score:
            self.dealer.add_card(self.deck.draw())
        if self.dealer.score > 21:
            self.view.player_won(self.state)
        if 21 >= self.dealer.score > self.player.score:
            self.view.player_lost(self.state)

    def player_plays(self):
        """"Model of player playing."""
        while True:
            if self.player.score > 21:
                self.view.player_lost(self.state)
                break
            if self.player.score == 21:
                self.view.player_won(self.state)
                break
            output = self.view.ask_next_move(self.state)
            if output == "H":
                self.player.add_card(self.deck.draw())
            if output == "S":
                break

    def state(self):
        """"Return state."""
        return self.state


class BlackjackView:
    """Minimalistic UI/view for the blackjack game."""

    def ask_next_move(self, state: dict) -> str:
        """
        Get next move from the player.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        :return: parsed command that user has choses. String "H" for hit and "S" for stand
        """
        self.display_state(state)
        while True:
            action = input("Choose your next move hit(H) or stand(S) > ")
            if action.upper() in ["H", "S"]:
                return action.upper()
            print("Invalid command!")

    def player_lost(self, state):
        """
        Display player lost dialog to the user.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        """
        self.display_state(state, final=True)
        print("You lost")

    def player_won(self, state):
        """
        Display player won dialog to the user.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        """
        self.display_state(state, final=True)
        print("You won")

    def display_state(self, state, final=False):
        """
        Display state of the game for the user.

        :param state: dict with given structure: {"dealer": dealer_hand_object, "player": player_hand_object}
        :param final: boolean if the given state is final state. True if game has been lost or won.
        """
        dealer_score = state["dealer"].score if final else "??"
        dealer_cards = state["dealer"].cards
        if not final:
            dealer_cards_hidden_last = [c.__repr__() for c in dealer_cards[:-1]] + ["??"]
            dealer_cards = f"[{','.join(dealer_cards_hidden_last)}]"

        player_score = state["player"].score
        player_cards = state["player"].cards
        print(dedent(
            f"""
            {"Dealer score":<15}: {dealer_score}
            {"Dealer hand":<15}: {dealer_cards}

            {"Your score":<15}: {player_score}
            {"Your hand":<15}: {player_cards}
            """
        ))


if __name__ == '__main__':
    BlackjackController(Deck(), BlackjackView())  # start the game.
