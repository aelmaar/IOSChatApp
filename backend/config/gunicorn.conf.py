import multiprocessing

bind = '0.0.0.0:8000'

workers = multiprocessing.cpu_count() * 2 + 1

reload = True

loglevel = 'info'

accesslog = '/var/log/gunicorn/access.log'
errorlog = '/var/log/gunicorn/error.log'

daemon = False
