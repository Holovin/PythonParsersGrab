from helpers.config import Config


def cookies_init(cookie_jar, g):
    if cookie_jar:
        g.cookies.cookiejar = cookie_jar

    cookie_name = Config.get('APP_COOKIE_NAME', '')
    cookie_value = Config.get('APP_COOKIE_VALUE', '')

    if cookie_name != '' and cookie_value != '':
        g.setup(cookies={cookie_name: cookie_value})

    return g
