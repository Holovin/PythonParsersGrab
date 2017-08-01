def check_body_errors(self, task, doc, part):
    """
    Check server response for errors

    :param self:
        Class instance for logger
    :param task:
        Grab task instance for get url
    :param doc:
        Server response
    :param part:
        String method name for logger
    :return:
        True if request failed
    """

    if doc.body == '' or doc.code != 200:
        err = '{} Code is {}, url is {}, body is {}'.format(part, doc.code, task.url, doc.body)
        print(err)
        self.logger.error(err)
        return True

    return False
