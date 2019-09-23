from threading import Thread, current_thread, Barrier, Lock
import time
from random import randint
from store.models import *
from store.backend import *
from store.store_exceptions import *
from math import ceil, floor
from decimal import Decimal

class StressTester(Thread):
    def __init__(self, user, min_sleep, max_sleep, barrier, lock, iterations):
        super().__init__()
        self.min_sleep = min_sleep
        self.max_sleep = max_sleep
        self.barrier = barrier
        self.lock = lock
        self.iterations = iterations
        self.user = user
        self.sequence = []
        self.products = []
        self.users = []

    def run(self):
        self.buildLists()
        self.generateSequence()
        user = list(User.objects.filter(id=self.user))[0]
        self.barrier.wait()
        actions = []
        for action in self.sequence:
            if action == 'buy':
                product = self.products[randint(0, len(self.products) - 1)]
                product = list(Product.objects.filter(id=product))[0]
                try:
                    for i in range(0, randint(0, 10)):
                        self.buy(product.id)
                except UserNotEnoughMoney:
                    charge_amount = Decimal(str(randint(ceil(product.price), 50)) + "." + str(randint(0, 99)))
                    self.charge(charge_amount)
                    self.buy(product.id)
                    actions.append('charged {}'.format(charge_amount))
                except IntegrityError:
                    pass
                actions.append('bought {} for {}'.format(product.name, product.price))
            else:
                receiver = self.users[randint(0, len(self.users) - 1)]
                transfer_amount = randint(1, floor(user.money))
                try:
                    for i in range(0, randint(0, 10)):
                        self.transfer(receiver, transfer_amount)
                except UserNotEnoughMoney:
                    charge_amount = Decimal(str(randint(ceil(transfer_amount), 50)) + "." + str(randint(0, 99)))
                    self.charge(charge_amount)
                    self.transfer(receiver, randint(1, floor(user.money)))
                    actions.append('charged {}'.format(charge_amount))
                except IntegrityError:
                    pass
                actions.append('transfered {} to {}'.format(transfer_amount, receiver))
        self.lock.acquire()
        print("Thread {} running for user '{}' (id: {}):".format(current_thread().ident, user.username, user.id), actions)
        self.lock.release()


    def buildLists(self):
        users = User.objects.exclude(id=self.user).values('id')
        self.users = [u['id'] for u in users]
        products = Product.objects.all().values('id')
        self.products = [p['id'] for p in products]


    def generateSequence(self):
        for i in range(0, self.iterations):
            if randint(0, 4) <= 2:
                self.sequence.append('buy')
            else:
                self.sequence.append('transfer')

    def buy(self, product):
        token = TokenLogic.get_token()
        self.wait()
        PurchaseLogic.purchase(self.user, product, token)
        self.wait()

    def transfer(self, receiver, amount):
        token = TokenLogic.get_token()
        self.wait()
        TransferLogic.transfer(self.user, receiver, amount, token)
        self.wait()

    def charge(self, amount):
        token = TokenLogic.get_token()
        self.wait()
        ChargeLogic.charge(self.user, amount, token)
        self.wait()
    
    def wait(self):
        time.sleep(randint(self.min_sleep, self.max_sleep + 1))

