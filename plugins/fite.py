from wrappers import *
import random

@plugin
class fite:
    actions = [
        '''clobbers {target}''',
        '''pinches {target}'s nipple''',
        '''pulls {target}'s hair''',
        '''gives {target} a wedgie''',
        '''sticks his tongue out at {target}''',
        '''moons {target}''',
        '''slaps {target}''',
        '''fites {target} IRL''',
        '''gives {target} a wet-willy''',
        '''tickles {target}''',
        '''pokes {target}''',
        '''smashes {target}'s face in with a brick in a sock''',
        '''slaps {target} with a fish''',
        '''punches {target}''',
        '''sets {target} on fire''',
        '''pushes {target} down a well''',
        '''glares at {target}''',
        '''farts in {target}'s general direction''',
        '''fires a water pistol at {target}''',
        '''fires a elastic band at {target}''',
        '''dunks {target} in syrup''',
        '''ties {target} over an anthill and puts honey on {target}'s genitalia''',
        '''ties {target} up and leaves them in the desert''',
        '''puts a bounty on {target}''',
        '''fires missiles at {target}'s location''',
        '''straps TNT to {target}'s chest''',
        '''pours poison in {target}'s drink''',
        '''triggers world war III, everyone VS {target}''',
        '''forces {target} to watch my little pony''',
        '''throws grass at {target}''',
        '''gives {target} cement shoes and throws them in the canal''',
        '''causes {target}'s seat to turn into jelly''',
        '''dribbles''',
        '''forces {target} to use OpenBSD''',
        '''takes a blunt rusty spoon and...''',
        '''joyously cries {target}, {target}, {target}!''',
        '''grumbles and mutters something about {target}, from his corner''',
        '''gives {target} a damn good thrashing''',
        '''moves knight to king's bishop three''',
        '''cuts the brake pipes on {target}'s car''',
        '''drop kittens on {target}'s head.''',
        '''cuddles {target}.''',
        '''farts on {target}'s head''',
        '''snuggles up to {target} and purrrrrrs''',
        '''slowly squeezes {target} until he pops!''',
        '''cries "Look out! Look out! The {target} s'about!"''',
        '''lightly chews on {target}''',
        '''stares intensively at {target} until their head explodes. (This could take a long time.)''',
        '''fiddles with his foo.''',
        '''urges {target} to repent and open your heart to the ways of the Unix command line.''',
        '''comments on {target}'s funny smell, kind of like beetroot.''',
        '''launches a cow into {target}'s fort''',
        '''jumps down from his tree and smashes {target}'s head in whith a coconut.''',
        '''waxes {target}'s legs''',
        '''waxes {target}'s anus''',
        '''waxes {target}'s face''',
        '''plucks {target}'s nose hairs''',
        '''waxes {target}'s anus''',
        '''hacks into SDS and changes {target}'s grade to zeros''',
        '''hugs {target}''',
        '''suggestively wiggles at {target}''',
        '''throws snot at {target}''',
        '''consumes {target}'s soul''',
        '''takes on the form of {target} and takes over their life''',
        '''puts something where he shouldn't''',
        '''puts something where {target} likes it''',
        '''steals {target}'s nose''',
        '''unleashes the flying monkeys''',
        '''deletes {target}'s file system''',
        '''replaces {target}'s computer with a potato''',
        '''steals {target}'s shoes''',
        '''noms on {target}''',
        '''punctures {target}'s tyres''',
        '''eats {target}'s pudding''',
        '''does a funny dance''',
        '''slams {target} with the arch manual, oh wait''',
        '''forces {target} to use Open BSD''',
        '''forces {target} to use Free BSD''',
        '''forces {target} to use Solaris''',
        '''forces {target} to use Windows''',
        '''forces {target} to use a Mac''',
        '''forces {target} to use OS2''',
        '''uses the force on {target}''',
        '''replaces {target}'s knees with {target}'s elbows''',
        '''licks {target}''',
        '''mooshes a bananna into {target}'s face''',
        '''Blasts {target} in the chest with a plasma caster.''',
        '''Blasts {target} in the mouth. TWICE!''',
        '''kicks {target}''',
        "Puts ants in {target}'s pants",
        '''Hides {target}'s keys''',
        '''Put's {target}'s shoes back on the shoe rack, but doesn't tell {target}, so {target} spends ages looking in all the wrong places.''',
        '''Puts ants in {target}'s pants''',
        '''Inserts a penny into {target}'s nose''',
        '''Brings the cage of japanese fighting spiders down on {target}.''',
        '''Subscribes {target} to UKIPs mailing list.''',
        '''Installs a tallbar into {target}'s browser.''',
        ''':{sender} Calls {bot} to fite {target}. {bot} Ignore him.''',
        '''Hides in teh corner.''',
        '''puts 'Let it Go' on repeat.''',
        '''puts on his fighting trousers.''',
        '''puts on his time-travel trousers.''',
        '''gets distracted by a nice cup of tea.''',
        '''chases {target}, but doesn't get very far because some cheeky scamp tied {bot}'s shoelaces together.''',
        '''ships something deadly to {target} via Yodel. Don't worry it probably won't arrive.''',
        '''slaps {target} round the face with a fresh mackerel.''',
        '''slaps {target} round the face with a slightly old Salmon.''',
        '''slaps {target} round the face with a can of Tuna.''',
        '''slaps {target} round the face with the left overs from a fish pie.''',
        '''replaces {target}'s mouse with a live mouse.''',
        '''inserts a USB plug correctly the first time, and is so excited that he forgets all about {target}.''',
        '''fires off his Rube Goldberg machine. Though complicated, and made of many parts it worked flawlessly, however the end result of a fried egg isn't that helpful.''',
        '''was a pacifist, untill you discovered democracy.''',
        '''sets his phaser to stun and shoots {target}.''',
        '''sets his phaser to heat and shoots {target}.''',
        '''sets his phaser to kill and shoots {target}.''',
        '''sets his phaser to disintegrate and shoots {target}.''',
        '''has a rather nasty poo in {target}'s toilet, and doesn't flush.''',
        '''replaces all {target}'s beer with Fosters.''',
        '''subcribes {target} to cat facts.''',
        '''tunes {target}'s radio into radio4.''',
        '''tunes {target}'s radio into radio1.''',
        '''tunes {target}'s radio into classic FM.''',
        '''takes {target} on a trip to the nearby planes.''',
        '''takes {target} on a trip to the mystery island of mystery.''',
        '''repaints {target}'s house in military grey.''',
        '''repaints {target}'s house in ocean grey.''',
        '''calls your Meemaw a bad word.''',
        '''eats {target}'s liver with some fava beans and a nice chianti''',
        '''writes "I AM A FISH" four hundred times, does a funny little dance and faints!''',
        '''Thinks it is time for WOO.''',
        '''drops the base on {target}''',
        '''drop the bass on {target}''',
        '''knows exactly how fast {target} is traveling. However he has no idea where {target} is.''',
        '''minaturises {target} and then looses them in the garden.''',
        '''does that thing with his tenticles you only see in japanese films.''',
        '''torrents music on {target}'s eduroam account.''',
        '''hoses {target} down.''',
        '''suggests a full frontal assault against {target} with automated laser monkeys, scalpel mines and acid.’''',
        '''suggest that he will melt {target} brain using projectile acid fish, and then interrogate them. [PAUSE] Other way round.’''',
        '''poisons {target}'s arse with poisonous gases (with traces of lead).''',
        '''snapchats {target} with a picture of his junk.''',
        '''performs a blood eagle on {sender}.''',
        '''recreates that scene from game of thrones, the one with Ramsey Snow, wiggle wiggle.''',
        '''kills {target} with a crossbow whilst {target} is sitting on the shitter.''',
        '''burns {target} at the stake.''',
        '''burns {target}'s steak.''',
        '''skins {target}.''',
        '''pours boiling tar on {target}.''',
        '''pours molton cheese on {target}.''',
        '''gives {target} a cup of tea, which {target} proceeds to burn his tounge on.''',
        '''tars and feathers {target}''',
        '''strips {target} naked and chases them down the street.''',
        '''melts {target}'s face with a mighty scream.''',
        '''melts {target}''',
        '''dismembers {target}''',
        '''jumps out on {target} from behind a corner.''',
        '''mixes up the love letter for {sender} with the hate mail for {target}.''',
        '''drinks {target} through a straw.''',
        '''disolves {target} in acid.''',
        '''squirts lemon juice in {target}'s eyes''',
        '''gets a bot fly to lay an egg on {target}.''',
        '''scrapes his arse across {target}'s floor, like a dog with worms.''',
        '''lobotomises {target}''',
        '''drills through {target}'s scull and drinks their brain with a straw''',
        '''paints {target} like one of his french girls.''',
        '''sets Mr Fox on {target}.''',
        '''washes {target} with hot soapy water, and and a brillo pad.''',
        '''fills {target} with helium and flies them like a balloon.''',
        '''paints a target on {target}'s chest and plays Robin Hood.''',
        '''waxes {target}'s big toes.''',
        '''Replicates that thing from the "The Following: Boxed in" on {target}. *shudders*''',
        '''Pours butter on {target}.''',
        '''Ghosts {target}.''',
        '''K-Lines {target}.''',
        '''casts penis of the infinite on {target}''',
        '''crushes {target}'s skull with his bare hands.''',
        '''Ties {target} up in ropes.''',
        '''Ties {target}'s shoelaces together''',
        '''pees in {target}'s soup.''',
        '''stack overflows.''',
        '''paints an erotic picture of {target} using his own blood.''',
        '''paints an picture of {target} using marmite.''',
        '''sends a sarcastic tweet to {target}''',
        '''breaks {target}'s ankles. misery style.''',
        '''Lauches {target} into space.''',
        '''Fires {target} at the sun.''',
        '''double frees {target}''',
        '''puts {target} in a giant shredder.''',
        '''sends {target} to Medway.''',
        '''sets the dogs on {target}.''',
        '''puts {target} in an apple press and squeezes''',
        '''straps {target} to a table with a slowing moving laser cutter.''',
        '''straps {target} to a tablesaw.''',
        '''teliports {target} into deep space.''',
        '''howls at the moon. {target} seems unperturbed.''',
        '''The villagers think {target} must be a werewolf, so {target} gets lynched.''',
        '''unplugs {target} from the matrix.''',
        '''stomps on {target}'s head.''',
        '''gives {target} x-ray vision, all their friends get cancer.''',
        '''sends {target}'s browser history to their mother.''',
        '''rub's tinfoil over {target}'s fillings.''',
        '''shoots {target}.''',
        '''Kills {target} till they are dead.''',
        '''Straps {target} to the church steeple during a thunder storm.''',
        '''attaches electrodes to {target}'s nipples.''',
        '''ties {target} to 4 sledge dog packs and yell MUSH.''',
        ]

    messages = [
        '''Mr Flibble is very cross, you shouldn't have run away from him. What are we going to do with {target} Mr Flibble?''',
        '''RIP {target}''',
        '''questions you this: given that God is infinite, and that the Universe is also infinite...would you like a toasted teacake?''',
        '''{target} might not be able to fight like a samurai, but you can at least die like a samurai.''',
        '''They do say, {sender}, that verbal insults hurt more than physical pain. They are, of course, wrong, as you will soon discover when I stick this toasting fork into {target}'s head.''',
        '''Don't worry {sender} I have a cunning plan!''',
        '''{target} is dead, {sender}. Everybody is dead. Everybody is dead, {sender}.''',
        '''It's all violence, violence, violence with you {sender}''',
    ]


    def random_response(self):
        max = len(self.messages) + len(self.actions)
        number = random.randint(0,max-1)

        if number >= len(self.messages):
            return True, self.actions[number-(len(self.messages))]
        else:
            return False, self.messages[number]

    @command("fighte")
    @command("fight")
    @command
    def fite(self, message):
        #assert isinstance(message.data,str), ValueError("needs to be a string")
        nicks = [nick for nick, user in self.bot.users[message.server].items() if message.params in user.channels[message.server] and nick != self.bot.servers[message.server].nick]
        data = {
            "sender": message.nick,
            "bot": self.bot.servers[message.server].nick,
            "channel": message.params,
            "server": message.server,
            "random": random.choice(nicks),
        }

        if message.data.split():
            for nick in message.data.split():
                action, response = self.random_response()
                if action:
                    yield message.reply(response.format(target=nick, **data), ctcp="ACTION")
                else:
                    yield message.reply(response.format(target=nick, **data))
        else:
            nicks = [nick for nick, user in self.bot.users[message.server].items() if message.params in user.channels[message.server] and nick != self.bot.servers[message.server].nick]
            nick = random.choice(nicks)
            action, response = self.random_response()
            if action:
                yield message.reply(response.format(target=nick, **data), ctcp="ACTION")
            else:
                yield message.reply(response.format(target=nick, **data))

    @trigger(lambda message, bot: message.ctcp=="ACTION" and bot.servers[message.server].nick in message.text)
    def fiteback(self, message):
        nicks = [nick for nick, user in self.bot.users[message.server].items() if message.params in user.channels[message.server] and nick != self.bot.servers[message.server].nick]
        data = {
            "sender": message.nick,
            "bot": self.bot.servers[message.server].nick,
            "channel": message.params,
            "server": message.server,
            "random": random.choice(nicks),
        }
        action, response = self.random_response()
        if action:
            yield message.reply(response.format(target=message.nick, **data), ctcp="ACTION")
        else:
            yield message.reply(response.format(target=message.nick, **data))
