import re
from collections import defaultdict
import random
from random import uniform
import conf
import telebot
import flask

r_alphabet = re.compile(u'[а-яА-Я0-9-]+|[.,:;?!]+')
bot = telebot.TeleBot(conf.TOKEN, threaded=False)
WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)
app = flask.Flask(__name__)
home_dir = '/home/marole/mysite/'
books = ['Игра Престолов.txt', 'Битва Королей часть 1.txt', 'Битва Королей часть 2.txt', 'Буря Мечей часть 1.txt', /
         'Буря Мечей часть 2.txt', 'Пир Стервятников.txt', 'Танец с Драконами часть 1.txt', 'Танец с драконами часть 2.txt']

def gen_lines(corpus):
    data = open(corpus)
    for line in data: #192842
        yield line.lower()


def gen_tokens(lines):
    for line in lines:
        for token in r_alphabet.findall(line):
            yield token

def gen_trigrams(tokens):
    t0, t1 = '$', '$'
    for t2 in tokens:
        yield t0, t1, t2
        if t2 in '.!?':
            yield t1, t2, '$'
            yield t2, '$','$'
            t0, t1 = '$', '$'
        else:
            t0, t1 = t1, t2

def train(corpus):
    lines = gen_lines(corpus)
    tokens = gen_tokens(lines)
    trigrams = gen_trigrams(tokens)

    bi, tri = defaultdict(lambda: 0.0), defaultdict(lambda: 0.0)

    for t0, t1, t2 in trigrams:
        bi[t0, t1] += 1
        tri[t0, t1, t2] += 1

    model = {}
    for (t0, t1, t2), freq in iter(tri.items()):
        if (t0, t1) in model:
            model[t0, t1].append((t2, freq/bi[t0, t1]))
        else:
            model[t0, t1] = [(t2, freq/bi[t0, t1])]
    return model

def generate_sentence(model):
    phrase = ''
    t0, t1 = '$', '$'
    while 1:
        t0, t1 = t1, unirand(model[t0, t1]) #unirand
        if t1 == '$': break
        if t1 in ('.!?,;:') or t0 == '$':
            phrase += t1
        else:
            phrase += ' ' + t1
    return phrase.capitalize()

def unirand(seq):
    sum_, freq_ = 0, 0
    for item, freq in seq:
        sum_ += freq
    rnd = uniform(0, sum_)
    for token, freq in seq:
        freq_ += freq
        if rnd < freq_:
            return token

@bot.message_handler(commands='start')
def send_welcome(message):
    bot.send_message(message.chat.id, 'Здравствуйте! Сейчас я буду с Вами разговаривать.')

@bot.message_handler(commands='help')
def send_help(message):
    bot.send_message(message.chat.id, 'Это бот, который на любое Ваше сообщение ответит фразой из "Песни Льда и Огня".')

@bot.message_handler(func=lambda m: True)
def send_phrase(message):
    book = random.choice(books)
    corpus = home_dir + book
    model = train(corpus)
    phrase = generate_sentence(model)
    bot.send_message(message.chat.id, phrase)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'

#if __name__ == '__main__':
#   bot.polling(none_stop=True)

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

