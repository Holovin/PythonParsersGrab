def get_body(grab, encoding='cp1251', bom=False, skip_errors=True, fix_spec_chars=True):
    return grab.doc.convert_body_to_unicode(grab.doc.body, bom, encoding, skip_errors, fix_spec_chars)
