import uuid

from django.core.management import call_command
from otree.models import Session
from .base import TestCase, TransactionTestCase
from otree.models.session import lock_on_this_code_path
import random
import threading
from django.conf import settings

def pick_random_winner():
        #with lock_on_this_code_path():
        session = Session.objects.get()
        subsession = session.get_subsessions()[0]
        if not subsession.winner_chosen:
            player = random.choice(subsession.get_players())
            player.is_winner = True
            player.save()
            subsession.winner_chosen = True
            subsession.save()

class TestLock(TransactionTestCase):

    def test_lock(self):
        # http://stackoverflow.com/q/11214099/38146
        if settings.DATABASES['default']['ENGINE'].endswith('sqlite3'):
            return

        call_command('create_session', 'multi_player_game', 6)

        NUM_THREADS = 3

        threads = []
        for i in range(NUM_THREADS):
            threads.append(
                threading.Thread(
                    target=pick_random_winner,
                )
            )
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        session = Session.objects.get()
        subsession = session.get_subsessions()[0]
        players = subsession.player_set.all()
        num_winners = sum([p.is_winner for p in players])
        # raise Exception(num_winners)
        self.assertTrue(num_winners == 1)

