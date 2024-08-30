class EntryCards():
    def __init__(self,user,cards,cardstext,cardsimages,in_db=False):
        self.user = user
        self.cards = cards
        self.cardstext = cardstext
        self.cardsimages = cardsimages
        self.in_db = in_db
    
    def get_cards(self):
        return [self.cards,self.cardstext,self.cardimages]
    
    def __str__(self):
        return str([self.user,self.cards])