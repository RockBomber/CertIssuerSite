# Описание

Web портал для генерации сертификата по файлу запроса на сертификат в формате PKCS#10

Файл `debug.sh` используется для запуска сервиса в отладочном режиме.

# 1. Установка на Ubuntu 20.04.1

1. Склонировать данный Git репозиторий в целевой каталог;
1. Перейти в каталог со склонированным репозиторием;
1. Создать вирутальное окружение Python и активировать его:\
`python3 -m venv .venv`
1. Установить зависимости:\
`pip install -r requirements.txt`
1. Настроить конфигурацию сервера в файле `config.py`
1. Проверить работоспособность сервера командой:\
`./server.py`\
и открыв страницу в браузере по порту 8080.
1. Проверить работоспособность gunicorn командой:\
`./debug.sh`\
и открыв страницу в браузере по порту 5000.
1. При необходимости настроить файл `supervisor.conf`
1. При необходимости настроить файл `nginx.conf`
1. Удалить дефолтный конфиг nginx из активных сайтов:\
`sudo rm /etc/nginx/sites-enabled/default`
1. Создать ссылку на конфиг nginx приложения:\
`sudo ln -s /opt/emulators/CertIssuerSite/nginx.conf /etc/nginx/sites-available/certissuersite.conf`
1. Создать ссылку на конфиг nginx активных сайтов:\
`sudo ln -s /etc/nginx/sites-available/certissuersite.conf /etc/nginx/sites-enabled/`
1. Перезапустить nignx:\
`sudo service nginx reload`
1. Создать ссылку на конфиг supervisord приложения:\
`sudo ln -s /opt/emulators/CertIssuerSite/supervisor.conf /etc/supervisor/conf.d/certissuersite.ini`
1. Обновить конфиг supervisord:\
`sudo supervisorctl update certissuersite`
1. Проверить работу сайта открыв страницу в браузере по порту 80.
