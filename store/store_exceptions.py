class UserNotEnoughMoney(Exception):
    def __init__(self):
        super().__init__("Guthaben reicht nicht aus!")
