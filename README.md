# selectel_storage

Пакет реализует поля к ORM для хрананение файлов приложения в облачном хранилище компании [Selectel](https://selectel.ru/)

Преимущества:
  1. Файлы храняться в формате gzip.
  2. В качестве имени берется md5 от контента файла, что бы избжать дубликатов
  3. Двух уровневая структура папок
  4. В базе данных храниться только путь до файла в хранилище

Для работы необходимо:
  1. Создать контейнер в обрачном хранилище
  2. Создать в облочном хранилище пользователя с правами доступа к этому контейнеру

## Установка
```
pip install selectel-storage
```

## Flask + MongoEngine
```python
import selectel_storage

from flask import Flask
from flask.ext.mongoengine import MongoEngine
from selectel_storage.flask import SelectelStorage

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'project1',
    'username':'webapp',
    'password':'pwd123'
}
app.config['SELECTEL_STORAGE'] = {
  'USER': 'username',
  'PASSWORD': 'password',
  'CONTAINER': 'images'
}

db = MongoEngine(app)
selectel = SelectelStorage(app)


class Images(db.Document):
    name = db.StringField()
    file = selectel.mongoengine.SelectelStorageField(root='images/')

```

Для создания объекта можно использовать стандартный FileHandler

```python
logo = open('logo.png', 'rb')
image = Image.objects.create(name='logo.png', file=logo)
```
также подойдут StringIO, TemporaryFile и любые другие объекты реализующие метод "read"

Дальшейшая работа с файлом ничем не отличается от работы со стандартным файловым объектом

Получение контена и его mimetype
```python
@app.route("/image/<image_id>")
def serve_image(image_id):
    image = Image.obkects.get_or_404(id=image_id)
    return Response(image.file.read(), mimetype=image.file.mimetype)
```

Удаление файла (полное удаление из облачного хранилища)
```python
image.file.delete()
```
**Внимание:** при удалении файла само поле file не изменяется и вызове метода "save()" файл вновь создатся.

