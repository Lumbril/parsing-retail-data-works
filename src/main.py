import re

from selenium import webdriver

BASE_URL = 'https://online.metro-cc.ru'
URL_CATEGORY = BASE_URL + '/category/myasnye/myaso'
driver = webdriver.Chrome()


def check_page(page: str):
    return '<p class="error-page__illustration-text" data-v-4be271cb="">' in page


def get_pages_count(url: str):
    driver.get(url)

    page = driver.page_source

    pagination_block = re.search(r'<ul.+class=\"catalog-paginate v-pagination\".+', page)[0]
    headers = re.findall(r'<a.+?>.+?</a>', pagination_block)

    page_numbers = [x for x in headers if 'svg' not in x]

    page_num = re.search(r'<a.+?>(.+?)</a>', page_numbers[-1]).group(1)

    return int(page_num)


def get_targets():
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


def collect_info(targets: list):
    driver.get(BASE_URL + targets[0])

    page = driver.page_source


def main():
    targets = get_targets()
    collect_info(targets)


if __name__ == '__main__':
    main()
