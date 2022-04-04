import json
import os

import requests as req

from config import Config


class YandexAPI:

    @staticmethod
    def get_pos(city):
        token = Config.YANDEX_API_TOKEN
        url_geo = f'https://geocode-maps.yandex.ru/1.x/'
        if not city:
            city = 'Ульяновск'
        url = url_geo + f'?apikey={token}&geocode={city}&format=json'
        try:
            response = req.get(url)
            if response.status_code != 200:
                raise Exception(response.status_code)
        except Exception as err:
            return dict(code=err)
        else:
            json_dir = os.path.join(f'{os.path.dirname(__file__)}', Config.YANDEX_API_JSON)
            count_json = len(os.listdir(json_dir))
            with open(f'{json_dir}/result_{count_json}.json', 'w', encoding='utf-8') as file:
                file.write(response.text)
            dict_res = json.loads(response.content)
            position = dict_res['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split(' ')
            longitude = position[0]
            width = position[1]
            return dict(code=response.status_code, data=dict_res, longitude=longitude, width=width)

    @staticmethod
    def get_map(longitude, width):
        token = Config.YANDEX_API_TOKEN
        url_static = f'http://static-maps.yandex.ru/1.x/'
        if not longitude or not width:
            longitude = 48.384824
            width = 54.151718
        spn = [0.3, 0.3]
        size_w = 450
        size_h = 450
        scheme_l = 'map'
        url = url_static + f'?apikey={token}&ll={longitude},{width}&' \
                                  f'spn={spn[0]},{spn[1]}&size={size_w},{size_h}&l={scheme_l}'
        try:
            response = req.get(url)
            if response.status_code != 200:
                raise Exception(response.status_code)
        except Exception as err:
            return dict(code=err, longitude=longitude, width=width)
        else:
            img_dir = os.path.join(f'{os.path.dirname(__file__)}', Config.YANDEX_API_IMG)
            count_img = len(os.listdir(img_dir))
            with open(f'{img_dir}/picture_{count_img}.jpg', 'wb') as file:
                file.write(response.content)
            return dict(code=response.status_code, img_name=f'picture_{count_img}.jpg')


