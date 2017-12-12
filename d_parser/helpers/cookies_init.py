# cookies_init.py
# Module for init cookies from config
# r1


from helpers.config import Config


def cookies_init(cookie_jar, grab):
    if cookie_jar:
        grab.cookies.cookiejar = cookie_jar

    cookie_name = Config.get('APP_COOKIE_NAME', '')
    cookie_value = Config.get('APP_COOKIE_VALUE', '')

    if cookie_name != '' and cookie_value != '':
        grab.setup(cookies={cookie_name: cookie_value})

    return grab


def cookies_init_v2(cookie_jar, grab):
    if cookie_jar:
        grab.cookies.cookiejar = cookie_jar

    cookies = Config.get_dict('APP_COOKIE_NAME', 'APP_COOKIE_VALUE')
    grab.setup(cookies=cookies)

    return grab
