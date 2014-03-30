import os
from eve import Eve

settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')

app = Eve(settings=settings_file)

if __name__ == '__main__':
    app.run()
