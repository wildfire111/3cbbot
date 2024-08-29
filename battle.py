class Battle:
    def __init__(self, player1_id, player2_id, resolved=False, points_player1=0, points_player2=0, in_db=False):
        """
        Initializes a Battle instance with the given players and status.

        Args:
            player1_id (str): Discord ID of the first player.
            player2_id (str): Discord ID of the second player.
            resolved (bool): Whether the battle has been resolved. Default is False.
            points_player1 (int): Points awarded to the first player. Default is 0.
            points_player2 (int): Points awarded to the second player. Default is 0.
            in_db (bool): Whether the battle is already in the database. Default is False.
        """
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.resolved = resolved
        self.points_player1 = points_player1
        self.points_player2 = points_player2
        self.in_db = in_db

    def resolve_battle(self, points_player1, points_player2):
        """
        Resolves the battle by setting the points for each player and marking it as resolved.

        Args:
            points_player1 (int): Points awarded to the first player.
            points_player2 (int): Points awarded to the second player.
        """
        self.points_player1 = points_player1
        self.points_player2 = points_player2
        self.resolved = True

    def mark_as_in_db(self):
        """
        Marks the battle as being saved in the database.
        """
        self.in_db = True

    def __repr__(self):
        """
        Provides a string representation of the Battle instance.
        """
        return (f"Battle(player1_id={self.player1_id}, player2_id={self.player2_id}, resolved={self.resolved}, "
                f"points_player1={self.points_player1}, points_player2={self.points_player2}, in_db={self.in_db})")
