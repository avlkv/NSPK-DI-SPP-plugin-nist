"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import logging
import requests
import time
import datetime
import dateutil.parser
import re
from bs4 import BeautifulSoup

from src.spp.types import SPP_document


class NIST:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """
    HOST = 'https://www.nist.gov/news-events/news'
    SOURCE_NAME = 'nist'
    TAGS: list[str] = [
        "<option value=249466>Advanced communications</option>",
        "<option value=248311>-Quantum communications</option>",
        # "<option value=248316>-Wireless (RF)</option>",
        # "<option value=248376>-Building codes and standards</option>",
        # "<option value=248381>-Building control systems</option>",
        # "<option value=248486>Electronics</option>",
        # "<option value=248491>-Electromagnetics</option>",
        # "<option value=248526>-Flexible electronics</option>",
        # "<option value=248496>-Magnetoelectronics</option>",
        # "<option value=248501>-Optoelectronics</option>",
        # "<option value=249491>-Organic electronics</option>",
        # "<option value=248511>-Semiconductors</option>",
        # "<option value=248516>-Sensors</option>",
        # "<option value=248521>-Superconducting electronics</option>",
        # "<option value=249421>Information technology</option>",
        # "<option value=2753736>-Artificial intelligence</option>",
        # "<option value=2800826>--AI measurement and evaluation</option>",
        # "<option value=2788806>--Applied AI</option>",
        # "<option value=2788801>--Fundamental AI</option>",
        # "<option value=2800831>--Hardware for AI</option>",
        # "<option value=2800991>--Machine learning</option>",
        # "<option value=2800836>--Trustworthy and responsible AI</option>",
        # "<option value=248701>-Biometrics</option>",
        # "<option value=248706>-Cloud computing and virtualization</option>",
        # "<option value=248711>-Complex systems</option>",
        # "<option value=248716>-Computational science</option>",
        # "<option value=248721>-Conformance testing</option>",
        # "<option value=248726>-Cyber-physical systems</option>",
        # "<option value=2746861>--Smart cities</option>",
        # "<option value=248731>-Cybersecurity</option>",
        # "<option value=248746>--Cryptography</option>",
        # "<option value=2753741>--Cybersecurity education and workforce development</option>",
        # "<option value=2788811>--Cybersecurity measurement</option>",
        # "<option value=248736>--Identity and access management</option>",
        # "<option value=2788816>--Privacy engineering</option>",
        # "<option value=248751>--Risk management</option>",
        # "<option value=2788821>--Securing emerging technologies</option>",
        # "<option value=2788826>--Trustworthy networks</option>",
        # "<option value=2788831>--Trustworthy platforms</option>",
        # "<option value=248756>-Data and informatics</option>",
        # "<option value=248761>--Human language technology</option>",
        # "<option value=248766>--Information retrieval</option>",
        # "<option value=248781>-Federal information processing standards (FIPS)</option>",
        # "<option value=248786>-Health IT</option>",
        # "<option value=2748441>-Internet of Things (IoT)</option>",
        # "<option value=248796>-Interoperability testing</option>",
        # "<option value=248801>-Mobile</option>",
        # "<option value=248806>-Networking</option>",
        # "<option value=2753766>--Mobile and wireless networking</option>",
        # "<option value=2753756>--Network management and monitoring</option>",
        # "<option value=248811>--Network modeling and analysis</option>",
        # "<option value=248771>--Natural language processing</option>",
        # "<option value=2753746>--Network security and robustness</option>",
        # "<option value=2753751>--Network test and measurement</option>",
        # "<option value=248816>--Next generation networks</option>",
        # "<option value=2753761>--Protocol&nbsp;design and standardization</option>",
        # "<option value=2753771>--Software defined and virtual networks</option>",
        # "<option value=248821>-Privacy</option>",
        # "<option value=248826>-Software research</option>",
        # "<option value=248841>--Software testing</option>",
        # "<option value=248846>-Usability and human factors</option>",
        # "<option value=248851>--Accessibility</option>",
        # "<option value=248776>-Video analytics</option>",
        # "<option value=2788836>-Virtual / augmented reality</option>",
        # "<option value=248856>-Visualization research</option>",
        # "<option value=248861>-Voting systems</option>",
        # "<option value=2748236>Infrastructure</option>",
        # "<option value=248936>-Technology commercialization</option>",
        # "<option value=249011>Mathematics and statistics</option>",
        # "<option value=249016>-Experiment design</option>",
        # "<option value=249021>-Image and signal processing</option>",
        # "<option value=249031>-Modeling and simulation research</option>",
        # "<option value=249036>-Numerical methods and software</option>",
        # "<option value=249041>-Statistical analysis</option>",
        # "<option value=249046>-Uncertainty quantification</option>",
        # "<option value=249341>Standards</option>",
        # "<option value=249346>-Accreditation</option>",
        # "<option value=249416>-Calibration services</option>",
        # "<option value=249366>-Conformity assessment</option>",
        # "<option value=249371>-Documentary standards</option>",
        # "<option value=2748516>-Frameworks</option>",
        # "<option value=249391>-Standards education</option>",
    ]
    _content_document: list[SPP_document]

    def __init__(self, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []

        # Логер должен подключаться так. Вся настройка лежит на платформе
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
        self._parse()
        self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        urls = []

        for i in range(len(self.TAGS)):
            splitter = "<option value=|>"
            massive_s = re.split(splitter, self.TAGS[i])
            number = massive_s[1]
            url = 'https://www.nist.gov/news-events/news/search?k=&t='
            req = requests.get(url + number)
            if req.status_code == 200:
                req.encoding = "UTF-8"
                soup = BeautifulSoup(req.content.decode('utf-8'), 'html.parser')
                try:
                    last_page = int(
                        soup.find('li', class_="pager__item pager__item--last").find('a')['href'].split('page')[1][1::])
                except AttributeError:
                    last_page = 0
                for j in range(last_page + 1):
                    req = requests.get(url + number + "&page=" + str(j))
                    req.encoding = "UTF-8"
                    soup = BeautifulSoup(req.content.decode('utf-8'), 'html.parser')
                    articles = soup.find_all('div', class_="nist-teaser__content-wrapper")
                    for article in articles:

                        news_date = datetime.datetime.strptime(article.find('time').text, '%B %d, %Y')

                        # Проверяем, что новость не ранее 01.01.2019
                        # if news_date > self.DATE_BEGIN:
                        #     # print(article.find('a')['href'])
                        urls.append("https://www.nist.gov" + article.find('a')['href'])
                            # print(article.find('a')['href'])
                    # print(url + number + "&page=" + str(j))
            else:
                # logger.error('Ошибка загрузки')
                ...

        new_urls = []
        for i in range(len(urls)):
            if not urls[i] in new_urls:
                # print(urls[i])
                new_urls.append(urls[i])

        for ref in (range(len(new_urls))):
            web_link = new_urls[ref]
            title, load_date, s_text, pub_date_text = self._document_parse(web_link)

            document = SPP_document(
                doc_id=None,
                title=title,
                abstract=None,
                text=s_text,
                web_link=web_link,
                local_link=None,
                other_data={},
                pub_date=dateutil.parser.isoparse(pub_date_text),
                load_date=load_date
            )

            # Логирование найденного документа
            self.logger.info(self._find_document_text_for_logger(document))

            self._content_document.append(document)
            time.sleep(1)
        # ---
        # ========================================
        ...

    @staticmethod
    def _find_document_text_for_logger(doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def _document_parse(self, ref):
        """
        Метод для непосредственного парсинга важных данных документа по ссылке
        :param ref:
        :type ref:
        :return:
        :rtype:
        """
        try:
            ufr = requests.get(ref)  # делаем запрос
            ufr.encoding = 'utf-8'

            if ufr.status_code == 200:
                idk = ref.split("/")
                f_name = idk[-1]
                load_date = datetime.datetime.now()

                soup = BeautifulSoup(ufr.content.decode('utf-8'), 'html.parser')
                s_text = ""
                for j in soup.find_all("div", class_="text-with-summary"):
                    for link2 in j.find_all("p"):
                        s_text = s_text + link2.text
                s_text = s_text.replace('\n', ' ').replace('\t', ' ').replace("¶", " ").replace("▲", " ").replace(
                    '\xa0', ' ').replace('\r', ' ').replace('—', "-").replace("’", "'").replace("“", '"').replace("”",
                                                                                                                  '"').replace(
                    " ", " ")
                while '  ' in s_text:
                    s_text = s_text.replace('  ', ' ')

                div_datetime = soup.find("div", class_='font-heading-md')
                pub_date = div_datetime.find('time').attrs['datetime']

                return f_name, load_date, s_text, pub_date
            else:
                self.logger.debug(f'Document processing error. Returned status code {ufr.status_code}')
        except Exception as e:
            self.logger.debug(f'Document processing error. Exception {e}')
