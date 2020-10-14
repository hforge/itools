# Copyright (C) 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Import from the Standard Library
from os import listdir

# Import from itools
from itools.gettext import MSG
from itools.gettext import register_domain

# Register the application's domain
register_domain('__main__', 'locale')


def say_hello():
    message = MSG(u'Hello World')
    print(message.gettext())


def get_template(name):
    # What are the possibilities ?
    languages = [
        x.rsplit('.', 1)[1] for x in listdir('.') if x.startswith(name) ]
    # A good language ?
    language = select_language(languages)
    # No
    if language is None:
        # English ?
        if 'en' in languages:
            language = 'en'
        # No, the first one, ...
        else:
            language = languages[0]
    return '%s.%s' % (name, language)


def tell_fable():
    template = get_template('fable.xhtml')
    print(open(template).read())


say_hello()
tell_fable()

