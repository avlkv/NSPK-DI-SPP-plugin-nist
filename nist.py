"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import logging
import requests
import time
from datetime import datetime
import dateutil.parser
import re
from bs4 import BeautifulSoup

from src.spp.types import SPP_document
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class NIST:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """
    # HOST = 'https://www.nist.gov/news-events/news'
    SOURCE_NAME = 'nist'
    _content_document: list[SPP_document]

    def __init__(self, webdriver: WebDriver, url: str, max_count_documents: int = None,
                 last_document: SPP_document = None, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []
        self.driver = webdriver
        self.wait = WebDriverWait(self.driver, timeout=20)
        self._max_count_documents = max_count_documents
        self._last_document = last_document
        if url:
            self.URL = url
            if 'news-events' in self.URL:
                self.DOC_TYPE = 'NEWS'
            elif 'publications' in self.URL:
                self.DOC_TYPE = 'PUBS'
            else:
                raise ValueError('unknown document types in provided url (not news or publications)')
        else:
            raise ValueError('url must be a link to the swift topic main page')

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
            self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # URL - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.URL}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        self.driver.get(self.URL)

        for page in self._encounter_pages():

            links = self.driver.find_elements(By.CLASS_NAME, 'nist-teaser')
            for link in links:
                doc_link = link.find_element(By.TAG_NAME, 'a').get_attribute('href')
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.get(doc_link)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.nist-page__title')))

                title = self.driver.find_element(By.CLASS_NAME, 'nist-page__title').text
                pub_date = dateutil.parser.parse(
                    self.driver.find_element(By.TAG_NAME, 'time').get_attribute('datetime'))
                tags = self.driver.find_element(By.CLASS_NAME, 'nist-tags').text

                if self.DOC_TYPE == 'NEWS':
                    try:
                        abstract = self.driver.find_element(By.XPATH, '//*[contains(@class, \'nist-block\')]/h3').text
                    except:
                        self.logger.debug('Empty abstract')
                        abstract = None
                    text_content = self.driver.find_element(By.CLASS_NAME, 'text-with-summary').text
                    web_link = doc_link
                    other_data = {'tags': tags, 'author': None}

                elif self.DOC_TYPE == 'PUBS':
                    try:
                        abstract = self.driver.find_element(By.CLASS_NAME, 'text-with-summary').text
                    except:
                        self.logger.debug('Empty abstract')
                        abstract = None
                    text_content = None
                    try:
                        author = [auth.text for auth in self.driver.find_elements(By.CLASS_NAME, 'nist-author')]
                    except:
                        self.logger.debug('Empty author')
                        author = None
                    try:
                        pdf_link = self.driver.find_element(By.XPATH, '//a[contains(text(), \'doi\')]').get_attribute(
                            'href')
                        self.driver.get(pdf_link)
                        time.sleep(0.5)

                        if self.driver.current_url.endswith('.pdf'):
                            web_link = self.driver.current_url
                        else:
                            self.logger.debug('Publication doesn\'t have open pdf')
                            web_link = self.driver.current_url
                    except:
                        self.logger.debug('Empty doi link => web_link = doc_link (NIST pub page)')
                        web_link = doc_link

                    other_data = {'tags': tags, 'author': author}


                else:
                    raise Exception('unknown doc type')

                doc = SPP_document(None,
                                   title,
                                   abstract,
                                   text_content,
                                   web_link,
                                   None,
                                   other_data,
                                   pub_date,
                                   datetime.now())

                self.find_document(doc)

                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

        # ---
        # ========================================
        ...


    def _find_document_text_for_logger(self, doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def find_document(self, _doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self._last_document and self._last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self._last_document})")

        self._content_document.append(_doc)
        self.logger.info(self._find_document_text_for_logger(_doc))

        if self._max_count_documents and len(self._content_document) >= self._max_count_documents:
            raise Exception(f"Max count articles reached ({self._max_count_documents})")
