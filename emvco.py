"""
Парсер плагина SPP

1/2 документ плагина
"""
import logging
import os
import time

import dateparser
from selenium.webdriver.common.by import By

from src.spp.types import SPP_document


class EMVco:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'emvco'
    HOST = "https://www.emvco.com/specifications/"
    _content_document: list[SPP_document]

    def __init__(self, driver, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []
        self.driver = driver

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)

        # УДалить DRAFT
        logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        self.logger.addHandler(consoleHandler)
        #

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

        self.driver.get(
            "https://www.emvco.com/specifications/")  # Открыть первую страницу с материалами EMVCo в браузере
        time.sleep(3)

        try:
            cookies_btn = self.driver.find_element(By.CLASS_NAME, 'ui-button').find_element(By.XPATH,
                                                                                            '//*[text() = \'Accept\']')
            self.driver.execute_script('arguments[0].click()', cookies_btn)
            self.logger.info('Cookies убран')
        except:
            self.logger.exception('Не найден cookies')
            pass

        self.logger.info('Прекращен поиск Cookies')
        time.sleep(3)

        while True:

            self.logger.debug('Загрузка списка элементов...')
            doc_table = self.driver.find_element(By.ID, 'filterable_search_results').find_elements(By.TAG_NAME,
                                                                                                   'article')
            self.logger.debug('Обработка списка элементов...')

            # Цикл по всем строкам таблицы элементов на текущей странице
            for element in doc_table[:2]:

                element_locked = False

                try:
                    title = element.find_element(By.CLASS_NAME, 'title-name').text

                except:
                    self.logger.exception('Не удалось извлечь title')
                    title = ' '

                try:
                    version = element.find_element(By.CLASS_NAME, 'version').text
                except:
                    self.logger.exception('Не удалось извлечь version')
                    version = ' '

                try:
                    date_text = element.find_element(By.CLASS_NAME, 'published').text
                except:
                    self.logger.exception('Не удалось извлечь date_text')
                    date_text = ' '

                try:
                    date = dateparser.parse(date_text)
                except:
                    self.logger.exception('Не удалось извлечь date')
                    date = None

                try:
                    tech = element.find_element(By.CLASS_NAME, 'tech-cat').text
                except:
                    self.logger.exception('Не удалось извлечь tech')
                    tech = ' '

                try:
                    doc_type = element.find_element(By.CLASS_NAME, 'spec-cat').text
                except:
                    self.logger.exception('Не удалось извлечь doc_type')
                    doc_type = ' '

                book = ' '

                if len(element.find_elements(By.CLASS_NAME, 'not-available-download')) > 0:
                    element_locked = True
                elif len(element.find_elements(By.CLASS_NAME, 'available-download')) > 0:
                    element_locked = False
                else:
                    element_locked = True

                try:
                    web_link = element.find_element(By.TAG_NAME, 'a').get_attribute('data-post-link')
                except:
                    self.logger.exception('Не удалось извлечь web_link')
                    web_link = None

                self._content_document.append(SPP_document(
                    doc_id=None,
                    title=title,
                    abstract=None,
                    text=None,
                    web_link=web_link,
                    local_link=None,
                    other_data= {
                        'doc_type': doc_type,
                        'tech': tech,
                        'version': version,
                        'book': book,
                    },
                    pub_date=date,
                    load_date=None,
                ))

                # file_link_already_exists = False
                #
                # for i, df_row in df.iterrows():
                #     if not element_locked:
                #         if (df_row['web_link'] == web_link) or (df_row['title'] == title):
                #             self.logger.debug(
                #                 f'Ссылка на файл или заголовок уже есть в датафрейме: \"{title}\" ({web_link})')
                #             file_link_already_exists = True

                # self.logger.debug('Загрузка файла отменена')
                # else:
                #     self.logger.info(f'{date_text} -_- {title}')
                #     driver.execute_script("window.open('');")
                #     driver.switch_to.window(driver.window_handles[1])
                #
                #     loaded_files_before = [f for f in listdir(downloads_dir) if isfile(join(downloads_dir, f))]
                #
                #     driver.get(web_link)
                #     time.sleep(1)
                #
                #     terms_of_use_title =self.driver.find_elements(By.XPATH, '//h3[text() = \'EMVCo TERMS OF USE\']')
                #
                #     if len(terms_of_use_title) > 0:
                #         try:
                #             tos_cookies_btn =self.driver.find_element(By.CLASS_NAME, 'ui-button').find_element(By.XPATH,
                #                                                                                            '//*[text() = \'Accept\']')
                #             driver.execute_script('arguments[0].click()', tos_cookies_btn)
                #             self.logger.info('Cookies убран')
                #         except:
                #             self.logger.info('Не найден cookies')
                #         time.sleep(1)
                #         accept_btn =self.driver.find_element(By.XPATH, '//button[text() = \'Accept\']')
                #         driver.execute_script('arguments[0].click()', accept_btn)
                #
                #     self.logger.info(f'Загрузка файла по ссылке {web_link}')
                #
                #     download_wait(directory=downloads_dir, timeout=30)
                #
                #     loaded_files_after = [f for f in listdir(downloads_dir) if isfile(join(downloads_dir, f))]
                #
                #     # self.logger.info(f'Список файлов после загрузки: {loaded_files_after}')
                #
                #     loaded_files_list = list(set(loaded_files_after) - set(loaded_files_before))
                #
                #     if len(loaded_files_list) > 1:
                #         for loaded_file_name in loaded_files_list:
                #             for old_file_name in loaded_files_before:
                #                 if loaded_file_name.split(' ')[0] in old_file_name:
                #                     loaded_files_list.remove(loaded_file_name)
                #                     break
                #     try:
                #         filename = loaded_files_list[0]
                #         self.logger.info(f'Новый файл: {filename}')
                #     except:
                #         self.logger.error('Не удалось загрузить файл и/или найти его в папке. Документ пропущен.')
                #         driver.close()
                #         driver.switch_to.window(driver.window_handles[0])
                #         continue
                #
                #     time.sleep(1)
                #     # download_wait(directory = downloads_dir, timeout = 15)
                #
                #     file_path = os.path.join(downloads_dir, unquote(filename))
                #     """22. Локальная ссылка на файл"""
                #
                #     self.logger.info(f'Файл загружен: {file_path}')
                #
                #     # 1. Прочитать текст из pdf по локальной ссылке (куда только что был загружен файл)
                #     # В датафрейме сохранить текст
                #     if filename.endswith('.pdf'):
                #         try:
                #             raw_text = extract_text(file_path)
                #             """Необработанное содержимое документа, извлеченное из pdf"""
                #         except:
                #             self.logger.exception('Не удалось извлечь содержимое из файла!')
                #             driver.close()
                #             driver.switch_to.window(driver.window_handles[0])
                #             continue
                #     else:
                #         file_type = filename.split('.')[-1]
                #         self.logger.warning(f'Расширение файла (.{file_type}) пока не поддерживается. Файл пропущен')
                #         driver.close()
                #         driver.switch_to.window(driver.window_handles[0])
                #         continue
                #
                #     load_date = datetime.now()
                #     """23. Дата загрузки материала"""
                #
                #     # table_row = row - 1
                #     table_row = df.shape[0]
                #     """1. Номер документа в таблице"""
                #
                #     source_name = 'EMVCo'
                #     """2. Название источника (доп. поле на всякий случай)"""
                #
                #     abstract = ''
                #     """5. Аннотация к материалу"""
                #
                #     self.logger.debug('Добавление строки в таблицу...')
                #
                #     self.logger.debug('Добавление строки в датафрейм...')
                #
                #     abstract = ''
                #
                #     row_data_list = [table_row, title, date, abstract, raw_text, web_link, file_path, load_date,
                #                      doc_type, tech, version, book]
                #     self.logger.info(df.columns)
                #     df.loc[df.shape[0]] = row_data_list
                #
                #     counter += 1
                #
                #     driver.close()
                #     driver.switch_to.window(driver.window_handles[0])
                #
                #     self.logger.info('Переход на вкладку 0')

            try:
                pagination_arrow = self.driver.find_element(By.XPATH, '//a[contains(@data-direction,\'next\')]')
                self.driver.execute_script('arguments[0].click()', pagination_arrow)
                time.sleep(3)
                pg_num = self.driver.find_element(By.ID, 'current_page').text
                self.logger.info(f'Выполнен переход на след. страницу: {pg_num}')

            #                 if int(pg_num) > 5:
            #                     self.logger.info('Выполнен переход на 6-ую страницу. Принудительное завершение парсинга.')
            #                     break

            except:
                self.logger.exception('Не удалось найти переход на след. страницу. Прерывание цикла обработки')
                break

        # Логирование найденного документа
        # self.logger.info(self._find_document_text_for_logger(document))

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

    @staticmethod
    def some_necessary_method():
        """
        Если для парсинга нужен какой-то метод, то его нужно писать в классе.

        Например: конвертация дат и времени, конвертация версий документов и т. д.
        :return:
        :rtype:
        """
        ...

    @staticmethod
    def nasty_download(driver, path: str, url: str) -> str:
        """
        Метод для "противных" источников. Для разных источника он может отличаться.
        Но основной его задачей является:
            доведение driver селениума до файла непосредственно.

            Например: пройти куки, ввод форм и т. п.

        Метод скачивает документ по пути, указанному в driver, и возвращает имя файла, который был сохранен
        :param driver: WebInstallDriver, должен быть с настроенным местом скачивания
        :_type driver: WebInstallDriver
        :param url:
        :_type url:
        :return:
        :rtype:
        """

        with driver:
            driver.set_page_load_timeout(40)
            driver.get(url=url)
            time.sleep(1)

            # ========================================
            # Тут должен находится блок кода, отвечающий за конкретный источник
            # -
            # ---
            # ========================================

            # Ожидание полной загрузки файла
            while not os.path.exists(path + '/' + url.split('/')[-1]):
                time.sleep(1)

            if os.path.isfile(path + '/' + url.split('/')[-1]):
                # filename
                return url.split('/')[-1]
            else:
                return ""
