## Как это работает?

![architecture.drawio.png](architecture.drawio.png)
![Формирование строки](https://habrastorage.org/getpro/habr/upload_files/adf/c03/870/adfc0387035178b57d44b5b4eae4b9c3.gif)

Подробнее об том, как примерно работает vosk-ai можно в [статье Яндекса](https://habr.com/ru/companies/yandex/articles/758782/)

### Требования:

Требует запущенного сервера Kaldi
https://alphacephei.com/vosk/install

Русская модель в Docker
https://hub.docker.com/r/alphacep/kaldi-ru

#### Библиотеки:
> asyncio, websockets, wave

#### Python:
> \>= 3.13.3 (рекомендуется)

#### Пример:
> Файл `transcription.txt` в корне репозитория, до обработки Gemini

> Файл `refactored.md` после обработки Gemini 2.5 Pro, Preview 05-06