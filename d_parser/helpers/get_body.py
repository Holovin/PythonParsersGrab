# TODO: remove useless params
def get_body(grab, encoding='cp1251', bom=False, skip_errors=True, fix_spec_chars=True):
    return grab.doc.body.decode('utf-8', 'ignore')
