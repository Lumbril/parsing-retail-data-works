import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver

import pandas as pd

from src.type_file import TypeFile


BASE_URL = 'https://online.metro-cc.ru'
URL_CATEGORY = BASE_URL + '/category/myasnye/myaso'
driver = webdriver.Chrome()


def check_page(page: str) -> bool:
    return '<p class="error-page__illustration-text" data-v-4be271cb="">' in page


def get_pages_count(url: str) -> int:
    driver.get(url)

    page = driver.page_source

    pagination_block = re.search(r'<ul.+class=\"catalog-paginate v-pagination\".+', page)[0]
    headers = re.findall(r'<a.+?>.+?</a>', pagination_block)

    page_numbers = [x for x in headers if 'svg' not in x]

    page_num = re.search(r'<a.+?>(.+?)</a>', page_numbers[-1]).group(1)

    return int(page_num)


def get_targets() -> list:
    targets = []

    for page_num in range(1, get_pages_count(URL_CATEGORY) + 1):
        driver.get(URL_CATEGORY + f'?page={page_num}')

        page = driver.page_source

        if check_page(page):
            return

        targets_from_page = re.findall(r'<a.+href=.+class=\"product-card-photo__link reset-link\"', page)
        targets_from_page = [re.search(r'href=\".+?\"', target)[0][6:-1] for target in targets_from_page]

        targets = targets + targets_from_page

    return targets


def get_product_id(page: str) -> int:
    soup = BeautifulSoup(page, 'html.parser')

    product_id = soup.find('p', class_='product-page-content__article').text.strip().\
        replace('\n', '').replace('Артикул: ', '')

    return int(product_id)


def get_product_name(page: str) -> str:
    soup = BeautifulSoup(page, 'html.parser')

    block = soup.find('h1', class_='product-page-content__product-name catalog-heading heading__h2')
    name = block.find('span').text.strip().replace('\n', '')

    return name


def get_product_actual_price(page: str) -> str:
    soup = BeautifulSoup(page, 'html.parser')

    block = soup.find('span',
                      class_=re.compile(r'product-price nowrap product-price-discount-above__actual-price+.*'))
    if block is not None:
        price = block.find('span', class_='product-price__sum-rubles').text.replace(u'\xa0', '')
    elif soup.find('p',
                   class_=re.compile(r'product-title product-page-content__title-out-of-stock+.*')) is not None:
        price = 'Раскупили'
    else:
        price = None

    return price


def get_product_old_price(page: str) -> str:
    soup = BeautifulSoup(page, 'html.parser')

    block = soup.find('span',
                      class_=re.compile(r'product-price nowrap product-price-discount-above__old-price+.*'))

    if block is not None:
        price = block.find('span', class_='product-price__sum-rubles').text.replace(u'\xa0', '')
        price = price
    else:
        price = None

    return price


def get_reg_and_promo_prices(page: str) -> list[str, str]:
    product_regular_price = get_product_actual_price(page)
    product_promo_price = get_product_old_price(page)

    return product_regular_price, product_promo_price


def get_product_brand(page: str) -> str:
    soup = BeautifulSoup(page, 'html.parser')

    block = soup.find('li', class_='product-attributes__list-item')
    brand = block.find('a', class_='product-attributes__list-item-link reset-link active-blue-text').text.strip()

    return brand


def get_product_info(url: str) -> list[int, str, str, str, str, str]:
    driver.get(BASE_URL + url)

    page = driver.page_source

    product_id = get_product_id(page)
    product_name = get_product_name(page)
    product_url = BASE_URL + url
    product_regular_price, product_promo_price = get_reg_and_promo_prices(page)
    product_brand = get_product_brand(page)

    return [product_id, product_name, product_url, product_regular_price, product_promo_price, product_brand]


def collect_info(targets: list, file_name='collect_info', type_file=TypeFile.CSV):
    collect_data = []
    average_time = 0

    for i in range(len(targets)):
        start = time.time()

        product_info = get_product_info(targets[i])

        collect_data.append(product_info)

        end = time.time() - start
        average_time += end

        print(f'{i + 1:3} : {len(targets):3}\ttime: {end:.5f}\tavg time: {average_time / (i + 1):.5f}')

    data = pd.DataFrame(collect_data, columns=['id', 'name', 'url', 'regular_price', 'promo_price', 'brand'])

    if type_file == TypeFile.CSV:
        data.to_csv(f'{file_name}.csv', index=False)
    elif type_file == TypeFile.JSON:
        data.to_json(f'{file_name}.json', index=False)
    elif type_file == TypeFile.XLSX:
        data.to_excel(f'{file_name}.xlsx', index=False)


def main():
    targets = get_targets()
    collect_info(targets)


if __name__ == '__main__':
    main()
