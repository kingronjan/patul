from lxml import etree

class Xpath(object):

    def __init__(self, text):
        self._text = text
        self._html = None

    def __call__(self, syntax):
        if self._html is None:
            self._html = etree.HTML(self._text)
        return _XpathResultList(self._html.xpath(syntax))

class _XpathResultList(list):

    def get(self, default=None):
        if self.__len__() > 0:
            result = self[0]
            if isinstance(result, etree._Element):
                result = etree.tostring(result, encoding='utf-8').decode('utf-8')
            return result
        else:
            return default

    def getall(self):
        return self