class EntryCards():
    def __init__(self,user,card1,card2,card3,in_db=False):
        self.user = user
        self.card1 = card1
        self.card2 = card2
        self.card3 = card3
        self.in_db = in_db
        self.card1text = ""
        self.card2text = ""
        self.card3text = ""
        self.card1url = ""
        self.card2url = ""
        self.card3url = ""
    
    def get_cards(self):
        return [self.card1,self.card2,self.card3]