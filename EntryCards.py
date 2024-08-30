class EntryCards:
    """
    A class to represent an entry of cards submitted by a user.

    Attributes:
        user (int): The user's ID who submitted the entry.
        cards (list of str): A list of card names submitted by the user.
        cardstext (list of str): A list of card texts corresponding to the submitted cards.
        cardsimages (list of str): A list of URLs for card images corresponding to the submitted cards.
        in_db (bool): A flag indicating whether this entry has been stored in the database.

    Methods:
        get_cards(): Returns card details as a list of lists.
        __str__(): Returns a string representation of the EntryCards object.
    """

    def __init__(self, user, cards, cardstext, cardsimages, in_db=False):
        self.user = user
        self.cards = cards
        self.cardstext = cardstext
        self.cardsimages = cardsimages
        self.in_db = in_db

    def get_cards(self):
        """Return card details as a list of lists."""
        return [self.cards, self.cardstext, self.cardsimages]

    def __str__(self):
        """Return a string representation of the EntryCards object."""
        return f"User: {self.user}, Cards: {self.cards}, In DB: {self.in_db}"
