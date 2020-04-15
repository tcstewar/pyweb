import js
jq = js.jQuery
q = js.query
import collections
import random

colors = 'kwrgb'

Noble = collections.namedtuple('Noble', ['points',
                                       'k', 'w', 'r', 'b', 'g'])
Card = collections.namedtuple('Card', ['level', 'bonus', 'points',
                                       'k', 'w', 'r', 'b', 'g'])
template_nobles = [[3,3,3,0,0, 3],
                   [4,4,0,0,0, 3],
                  ]
def generate_nobles():
    nobles = []
    for i, color in enumerate(['w', 'k', 'r', 'g', 'b']):
        for data in template_nobles:
            n = Noble(points=data[5],
                      w=data[(0+i)%5],
                      k=data[(1+i)%5],
                      r=data[(2+i)%5],
                      g=data[(3+i)%5],
                      b=data[(4+i)%5])
            nobles.append(n)
    return nobles


template_cards = {
    1: [[0,1,0,2,2, 0],
        [0,1,2,0,0, 0],
        [0,1,1,1,1, 0],
        [0,0,0,0,3, 0],
        [0,0,0,2,2, 0],
        [0,1,1,2,1, 0],
        [3,1,0,0,1, 0],
        [0,0,0,4,0, 1],
        ],
    2: [[0,2,2,3,0, 1],
        [2,0,3,0,3, 1],
        [0,2,4,1,0, 2],
        [0,0,5,0,0, 2],
        [0,3,5,0,0, 2],
        [6,0,0,0,0, 3],
        ],
    3: [[0,3,5,3,3, 3],
        [0,7,0,0,0, 4],
        [3,6,3,0,0, 4],
        [3,7,0,0,0, 5],
        ],
    }

def generate_cards():
    cards = []
    for i, color in enumerate(['w', 'k', 'r', 'g', 'b']):
        for level, templ in template_cards.items():
            for data in templ:
                c = Card(level=level, bonus=color, points=data[5],
                         w=data[(0+i)%5],
                         k=data[(1+i)%5],
                         r=data[(2+i)%5],
                         g=data[(3+i)%5],
                         b=data[(4+i)%5])
                cards.append(c)
    return cards



class Player(object):
    def __init__(self, game):
        self.game = game
        self.chips = {c:0 for c in colors+'x'}
        self.bonus = {c:0 for c in colors}
        self.cards = []
        self.reserve = []
        self.nobles = []
        self.points = 0

    def can_draw_three(self, **kwargs):
        if self.game.players[self.game.current_player] is not self:
            return False
        if self.game.must_select_noble:
            return False
        if sum(kwargs.values()) > 3:
            return False
        for c in colors:
            n = kwargs.get(c, 0)
            if n < 0 or n > 1 or n > self.game.chips[c]:
                return False
        return True

    def draw_three(self, **kwargs):
        assert self.can_draw_three(**kwargs)
        for c in colors:
            n = kwargs.get(c, 0)
            self.chips[c] += n
            self.game.chips[c] -= n
        self.game.end_turn()

    def can_draw_two(self, color):
        if self.game.players[self.game.current_player] is not self:
            return False
        if self.game.must_select_noble:
            return False
        if self.game.chips[color] < 4:
            return False
        return True

    def draw_two(self, color):
        assert self.can_draw_two(color)
        self.chips[color] += 2
        self.game.chips[color] -= 2
        self.game.end_turn()

    def can_reserve_card(self, card):
        if self.game.players[self.game.current_player] is not self:
            return False
        if self.game.must_select_noble:
            return False
        if len(self.reserve) >= 3:
            return False
        if not self.game.is_in_tableau(card):
            return False
        return True

    def reserve_card(self, card):
        assert self.can_reserve_card(card)
        self.reserve.append(card)
        self.game.remove_card(card)
        if self.game.chips['x'] > 0:
            self.game.chips['x'] -= 1
            self.chips['x'] += 1
        self.game.end_turn()

    def can_play(self, card):
        if self.game.players[self.game.current_player] is not self:
            return False
        if self.game.must_select_noble:
            return False
        if not self.game.is_in_tableau(card) and card not in self.reserve:
            return False
        extra_needed = 0
        for c in colors:
            cost = getattr(card, c)
            if self.chips[c] + self.bonus[c] < cost:
                extra_needed += cost - (self.chips[c] - self.bonus[c])
        if extra_needed > self.chips['x']:
            return False
        return True

    def play(self, card):
        assert self.can_play(card)
        self.cards.append(card)
        if card in self.reserve:
            self.reserve.remove(card)
        else:
            self.game.remove_card(card)
        for c in colors:
            cost = getattr(card, c)
            self.chips[c] -= max(cost - self.bonus[c], 0)
            self.game.chips[c] += max(cost - self.bonus[c], 0)
            if self.chips[c] < 0:
                self.chips['x'] += self.chips[c]
                self.game.chips[c] += self.chips[c]
                self.game.chips['x'] -= self.chips[c]
                self.chips[c] = 0
        self.bonus[card.bonus] += 1
        self.points += card.points
        self.check_nobles()
        if self.points >= 15:
            self.game.end_game = True
        self.game.end_turn()

    def check_nobles(self):
        my_nobles = []
        for n in self.game.nobles:
            for c in colors:
                if getattr(n, c) > self.bonus[c]:
                    break
            else:
                my_nobles.append(n)
        if len(my_nobles) == 1:
            n = my_nobles[0]
            self.nobles.append(n)
            self.game.nobles.remove(n)
            self.points += n.points
        elif len(my_nobles) > 1:
            self.game.must_select_noble = True
            self.game.selectable_nobles = my_nobles

    def can_select_noble(self, noble):
        if self.game.players[self.game.current_player] is not self:
            return False
        if not self.game.must_select_noble:
            return False
        if noble not in self.game.selectable_nobles:
            return False
        return True

    def select_noble(self, noble):
        assert self.can_select_noble(noble)
        self.nobles.append(noble)
        self.points += noble.points
        self.game.nobles.remove(noble)
        self.game.must_select_noble = False
        self.game.selectable_nobles = None

    def valid_actions(self):
        actions = []
        if self.game.must_select_noble:
            for n in self.game.selectable_nobles:
                actions.append((self.select_noble, dict(noble=n)))
            return actions

        for level in [1, 2, 3]:
            for card in self.game.tableau[level]:
                if card is not None:
                    if self.can_play(card):
                        actions.append((self.play, dict(card=card)))
        for card in self.reserve:
            if self.can_play(card):
                actions.append((self.play, dict(card=card)))
        for i, c1 in enumerate(colors):
            if self.game.chips[c1] == 0:
                continue
            for j, c2 in enumerate(colors[i+1:]):
                if self.game.chips[c2] == 0:
                    continue
                for c3 in colors[i+j+2:]:
                    if self.game.chips[c3] == 0:
                        continue
                    actions.append((self.draw_three, {c1:1, c2:1, c3:1}))
        for c in colors:
            if self.game.chips[c] >= 4:
                actions.append((self.draw_two, dict(color=c)))
        if len(self.reserve) < 3:
            for level in [3, 2, 1]:
                for card in self.game.tableau[level]:
                    if card is not None:
                        actions.append((self.reserve_card, dict(card=card)))
        return actions


class Splendor(object):
    def __init__(self, n_players, seed):
        self.players = [Player(self) for i in range(n_players)]
        rng = random.Random()
        rng.seed(seed)
        all_cards = generate_cards()
        rng.shuffle(all_cards)
        self.levels = {}
        self.tableau = {}
        for level in [1, 2, 3]:
            self.levels[level] = [x for x in all_cards if x.level==level]
            self.tableau[level] = [self.draw(level) for j in range(4)]

        all_nobles = generate_nobles()
        rng.shuffle(all_nobles)
        self.nobles = all_nobles[:n_players+1]
        self.must_select_noble = False

        self.first_player = rng.randrange(n_players)
        self.current_player = self.first_player
        self.end_game = False
        self.winners = None
        self.pass_count = 0

        n_chips = 7 if n_players > 2 else 4
        self.chips = dict(k=n_chips, w=n_chips, r=n_chips,
                          g=n_chips, b=n_chips, x=5)

    def draw(self, level):
        if len(self.levels[level]) == 0:
            return None
        return self.levels[level].pop()

    def is_in_tableau(self, card):
        for level in [1, 2, 3]:
            if card in self.tableau[level]:
                return True
        return False

    def remove_card(self, card):
        for level in [1, 2, 3]:
            if card in self.tableau[level]:
                self.tableau[level].remove(card)
                self.tableau[level].append(self.draw(level))
                return
        raise Exception('removed unknown card')

    def pass_turn(self):
        self.pass_count += 1
        if self.pass_count == len(self.players):
            self.winners = []
            self.current_player = None
        else:
            self.end_turn(reset_pass=False)

    def end_turn(self, reset_pass=True):
        if reset_pass:
            self.pass_count = 0
        self.current_player = ((self.current_player + 1) % len(self.players))
        if self.end_game and self.current_player == self.first_player:
            max_points = max([p.points for p in self.players])
            self.winners = [p for p in self.players if p.points == max_points]
            self.current_player = None



def text_game_state(game):
    rows = []
    n = ''.join('%14s' % text_noble(n) for n in game.nobles)
    rows.append(n)
    rows.append('-'*76)
    for level in [3, 2, 1]:
        lev = ''.join('%19s' % text_card(c) for c in game.tableau[level])
        rows.append(lev)
    rows.append('-'*76)

    chips = []
    for c in colors+'x':
        chips.append('%d%s' % (game.chips[c], c))
    rows.append('  '.join(chips))
    rows.append('='*76)



    for i, p in enumerate(game.players):
        current = '*' if game.current_player == i else ' '
        chip_info = []
        for c in colors:
            bonus = p.bonus[c]
            chips = p.chips[c]
            if bonus > 0:
                if chips > 0:
                    chip_info.append('%d[+%d]%s' % (chips, bonus, c))
                else:
                    chip_info.append('[+%d]%s' % (bonus, c))
            else:
                chip_info.append('%d%s' % (chips, c))
        if p.chips['x'] > 0:
            chip_info.append('%dx' % (p.chips['x']))
        if len(p.reserve) > 0:
            reserve = ' '.join(text_card(c) for c in p.reserve)
        else:
            reserve = ''
        if len(p.nobles) > 0:
            nobles = ' '.join(text_noble(n) for n in p.nobles)
        else:
            nobles = ''

        rows.append('%sP%d [%d] %s %s %s' % (current, i, p.points, 
                                            ':'.join(chip_info), nobles, reserve))

    return '\n'.join(rows)

def text_noble(noble):
    cost = []
    for c in colors:
        v = getattr(noble, c)
        if v > 0:
            cost.append('%d%s' % (v, c))
    return '[%d](%s)' % (noble.points, ':'.join(cost))


def text_card(card):
    if card is None:
        return '----'
    points = '+%d' % card.points if card.points > 0 else ''

    cost = []
    for c in 'kwrgb':
        v = getattr(card, c)
        if v > 0:
            cost.append('%d%s' % (v, c))

    return '[%s%s](%s)' % (card.bonus, points, ':'.join(cost))

def text_action(func, args):
    name = func.__name__
    if name == 'draw_three':
        return 'Draw Three: %s %s %s' % tuple(args.keys())
    elif name == 'draw_two':
        return 'Draw Two: %s' % args['color']
    elif name == 'reserve_card':
        return 'Reserve: %s' % text_card(args['card'])
    elif name == 'play':
        return 'Play: %s' % text_card(args['card'])
    else:
        return name, args
def code_action(func, args):
    name = func.__name__
    if name == 'draw_three':
        return 'd3:%s%s%s' % tuple(args.keys())
    elif name == 'draw_two':
        return 'd2:%s' % args['color']
    elif name == 'reserve_card':
        return 'r:%s' % text_card(args['card'])
    elif name == 'play':
        return 'p:%s' % text_card(args['card'])
    else:
        return name, args
        
        
def html_action(func, args):
    code = "act('%s')" % code_action(func, args)
    return '<li onclick="%s">%s</li>' % (code, text_action(func, args))

def act(code):
    p = game.players[game.current_player]
    actions = p.valid_actions()
    for f, a in actions:
        code2 = code_action(f, a)
        if code == code2:
            f(**a)
            update()
    
def update():
    txt = text_game_state(game)
    q('#board').html('<pre>%s</pre>'%txt)

    p = game.players[game.current_player]
    actions = p.valid_actions()
    q('#actions').html('<ul>%s</ul>'%''.join([html_action(*a) for a in actions]))


game = Splendor(n_players=1, seed=3)
update()




