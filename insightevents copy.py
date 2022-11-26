# -*- coding: utf-8 -*-
"""
@author: ChewingGumKing_OJF
"""
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from logging import Logger
from random import randint
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union

import requests
#loads necessary libraries
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

#*******************************************************************************************************************
sys.path.insert(
    0,
    os.path.dirname(__file__).replace('parsing-new-script', 'global-files/'))

#*******************************************************************************************************************

def creating_log(script_name: str, log_folder_path: Optional[str] = None):
    """ 
    Implements the logging module and returns the logger object. 
    Takes a string positional parameter for log file name and a keyword parameter for log file path. 
    Default log file path folder 'log_folder' and each code run clears the last log.
    """

    if not log_folder_path:
        log_folder_path: str = 'log_folder'

    if os.path.exists(log_folder_path):
        for files in os.listdir(log_folder_path):
            if files == f'{os.path.basename(__file__)}.log':
                os.remove(os.path.join(os.getcwd(), log_folder_path, files))
    else:
        os.makedirs(log_folder_path)

    log_path = os.path.join(os.getcwd(), log_folder_path, f'{script_name}.log')

    logger: Logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)
    log_handler = logging.FileHandler(log_path)
    log_format = logging.Formatter(
        '\n %(asctime)s -- %(name)s -- %(levelname)s -- %(message)s \n')
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    logger.info('Log reporting is instantiated.')

    return logger


logger = creating_log(f'{os.path.basename(__file__)}')
#*******************************************************************************************************************
import warnings

from GlobalFunctions import GlobalFunctions
from GlobalVariable import GlobalVariable

warnings.filterwarnings("ignore")

#*******************************************************************************************************************
def split_names(text):
    splitted = text.text.split('\n')
    if len(splitted) == 1:
        splitted.append('')
    return splitted

def date_transformation(date: str) -> Tuple[str, str]:
    match = re.search(r'(\d{1,2})-(\d{1,2})\s*(\w+)\s*(\d{4})', date)
    if match:
        change = lambda exact: datetime.strptime(exact, '%d %B %Y').strftime('%Y-%m-%d')
        return tuple(map(lambda no: change(' '.join(match.group(no, *(3, 4)))), [1, 2]))
#*******************************************************************************************************************

error: str = ''

try:
    file_name = sys.argv[1]  #file name from arguments (1st)
    port = int(sys.argv[2])  #port number from arguments (2nd)

    GlobalFunctions.createFile(
        file_name)  #to created TSV file with header line

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    #options.add_argument("--window-size=1920,1080")


    path = GlobalVariable.ChromeDriverPath
    driver = webdriver.Chrome(options=options, executable_path=path, port=port)

    @dataclass
    class ScrapeEvent:
        """ 
        The codebase design uses a single Class( dataclass) with it Methods as function scraping singular data (some more though).
        Returns the "self" to a it caller which is handled by a context manager.
        """

        browser: WebDriver = driver
        wait_5sec: WebDriverWait = WebDriverWait(browser, 5)
        error_msg_from_class: str = ''

        def __enter__(self) -> NoReturn:
            "Handles the contex manager."
            return self

        def __exit__(self, exc_type=None, exc_value=None, exc_tb=None) -> NoReturn:
            "Hanles the teardown of the context manager."
            self.browser.quit()

        def dispatch(self, locator:str, strategy:webdriver = By.CSS_SELECTOR) -> str:
            "API call for selenium.webdriver.remote.webelement.find_element(strategy, locator)"
            return self.browser.find_element(strategy, locator)

        def dispatchList(self, locator:str, strategy:webdriver = By.CSS_SELECTOR)  -> List:
            "API call for selenium.webdriver.remote.webelement.find_elements(strategy, locator)"
            return self.browser.find_elements(strategy, locator)


        def get_events(self, url: str) -> List[str]:
            "Returns a list of all urls"
            try:
                self.browser.get(url)
                time.sleep(1)
                self.dispatch('#cookie_action_close_header').click()
            except:
                pass
            try:
                all_url = [each.get_attribute('href') for each in self.dispatchList('.pt-cv-ifield>h4>a')]
                all_title = [each.text for each in self.dispatchList('.pt-cv-ifield>h4>a')]
                all_date = map(date_transformation, [each.text for each in self.dispatchList('.pt-cv-ifield .pt-cv-ctf-value>strong')])
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return list(zip(all_url, all_title, all_date))

        def get_dates(self) -> List[Tuple[str, str]]:
            "TScrapes and returns a list of date"
            try:
                all_dates = [each.text for each in self.dispatchList('.event-date')]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return list(map(date_transformation, all_dates))
        

        def get_event(self, url: str) -> NoReturn:
            "Get a singualr event from a list of all events"
            try:
                self.browser.get(url)
                time.sleep(1)
                self.dispatch('#cookie_action_close_header').click()
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
            
        
        
        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                sc_event_info = self.dispatch('.fusion-title-1').text 
            except Exception as e:
                try:
                    print('in here')
                    sc_event_info = self.dispatch('#ut_inner_column_637dff8bde2f0 p').text
                    return re.search(r'([^\?]+\?)', sc_event_info).group(1)
                except:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.exception(f'{self.event_info.__name__} Function failed')
            else:
                return sc_event_info


        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                price_t_1 = self.dispatch(".fusion-text tbody .row-1 .column-2").text
                price_v_1 = self.dispatch(".fusion-text tbody .row-2 .column-2").text.split(' ')
                price_t_2 = self.dispatch(".fusion-text tbody .row-1 .column-3").text
                price_v_2 = self.dispatch(".fusion-text tbody .row-2 .column-3").text.split(' ')
            except Exception as e:
                try:
                    price_t_1 = self.dispatch(".row-2 .column-1").text
                    price_v_1 = self.dispatch(".row-2 .column-2").text.split(' ')
                    price_t_2 = self.dispatch(".row-3 .column-1").text
                    price_v_2 = self.dispatch(".row-3 .column-2").text.split(' ')
                except:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
                else:
                    return [
                    {'type':price_t_1, 'price':price_v_1[0], 'currency':price_v_1[1]},
                    {'type':price_t_2, 'price':price_v_2[0], 'currency': price_v_2[1]}]
            else:
                return [
                    {'type':price_t_1, 'price':price_v_1[0], 'currency':price_v_1[1]},
                    {'type':price_t_2, 'price':price_v_2[0], 'currency': price_v_2[1]}]

        def event_mode(self) -> List[str]:
            "Scrapes and return event venue "
            try:
                location = self.dispatch(".link-type-text>.content-container p").text.split('\n')
            except Exception as e:
                try:
                    pass
                except:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
                else:
                    return ''
            else:
                return location
                    

        def contactmail(self) -> json:
            "Scrapes and return a JSONified format of event contact email(s)."
            try:
                contact_email = list(map(lambda e: e.text, self.dispatchList('.fusion-fullwidth.hundred-percent-fullwidth .fusion-one-third.fusion-column-last .fusion-text')))
                container = '\n'.join(contact_email).split('\n')
                filter_for_email = lambda var: '@' in var
                email_list = [mail.replace('Epost: ', '').replace('E-post: ', '') for mail in tuple(filter(filter_for_email, container))]
                if email_list == []:
                    raise IndexError()
            except Exception as e:
                try:
                    contact_email = self.dispatchList('#ut-row-6380cbca1a738 a')
                    contact_email = map(lambda e: e.text, contact_email)
                    contact_email = list(filter(lambda x: x != '', contact_email))
                except:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
                else:
                    return json.dumps(contact_email, ensure_ascii=False)
            else:
                return json.dumps(email_list, ensure_ascii=False)

        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                speaker_list = list(map(split_names, self.dispatchList('.fusion-one-fourth p[style="text-align: center;"]')))
                speaker_list = speaker_list[1:]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return list(map(lambda a: {'name':a[0], 'title': a[1]}, speaker_list))


        def google_map_url(self, search_word: str) -> str:
            """
            Returns the result of a Google Maps location search of the parameter.
            This implementation creates a new tab for it job, closes it when done and switch back handle to previous tab.
            """
            try:
                if search_word == 'ONLINE':
                    return 'ONLINE'

                curr_tab = self.browser.current_window_handle
                self.browser.switch_to.new_window('tab')

                map_url = GlobalFunctions.get_google_map_url(search_word, self.browser)

            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.google_map_url.__name__} Function failed', exc_info=True)

            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url


    base_url = 'https://insightevents.se/events/'

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        try:
            all_events = handler.get_events(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
            logger.exception(f'{handler.get_events.__name__} Function failed')
    # end of first part

    # second part
        for i in all_events:

            if i[0] == 'https://insightevents.se/events/battery-tech-for-ev/':
                continue
            try:
                try:
                    handler.get_event(i[0])
                    time.sleep(1)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.get_event.__name__} Function failed', exc_info=True)

                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = handler.browser.current_url

                # 2 BLOCK CODE: scraping attribute eventname
                try:
                    eventname = i[1]
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.eventname.__name__} Function failed', exc_info=True)
                    eventname = ''

                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    startdate = i[2][0]
                    enddate = i[2][1]
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_date.__name__} Function failed', exc_info=True)
                    startdate = ''
                    enddate = ''
                
            
                # 5 BLOCK CODE: scraping attribute timing
                try:
                    timing =''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_timing.__name__} Function failed', exc_info=True)
                    timing = ''


                # 6 BLOCK CODE: scraping attribute event_info
                try:
                    eventinfo = handler.event_info()
                    if not eventinfo:
                        eventinfo = f'Theme: {eventname.title()} + {startdate} - {enddate}'
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_info.__name__} Function failed', exc_info=True)
                    eventinfo = ''


                # 7 BLOCK CODE: scraping attribute ticketlist
                try:
                    ticketlist = handler.event_ticket_list()
                    if ticketlist:
                        ticketlist = json.dumps(ticketlist, ensure_ascii=False)
                    else: ticketlist = ''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_ticket_list.__name__} Function failed', exc_info=True)
                    ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'Insight Events Sweden AB (tidigare Informa IBC Sweden) startade sin verksamhet 1994 och genomför årligen ett flertal mässor, konferenser, kurser och utbildningar på den svenska marknaden. Våra tusentals deltagare är beslutsfattare från både privata näringslivet och offentlig sektor. Målsättningen är att ge våra deltagare ny och utvecklande kunskap med de mest kända experterna inom respektive område. Våra produkter erbjuder också möjlighet att personligen möta potentiella kunder och knyta nya affärskontakter.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'Insight Events'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://insightevents.se/'

                # 11 BLOCK CODE: scraping attribute logo
                logo = ''

                # 12 BLOCK CODE: scraping attribute sponsor
                sponsor = ''

                # 13 BLOCK CODE: scraping attribute agendalist
                agendalist = ''

                #14 BLOCK CODE: scraping attribute type
                type = ''
                #15 BLOCK CODE: scraping attribute category
                category = ''

                try:
                    mode = handler.event_mode()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)

                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                try:
                    if isinstance(mode, (tuple, list)):
                        venue = f'{mode[0]} {mode[1]}'
                        city = mode[2]
                        country = ''
                    elif isinstance(mode, str):
                        if mode == 'ONLINE':
                            venue = ''
                            city = ''
                            country = ''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)
                    venue = ''
                    city = ''
                    country = ''


                # 19 BLOCK CODE: scraping attribute event_website
                event_website = scrappedUrl

                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if venue:
                        sc_search_word = f'{venue}'
                        googlePlaceUrl = handler.google_map_url(sc_search_word)
                    else:
                        googlePlaceUrl = ''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.google_map_url.__name__} Function failed', exc_info=True)
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                try:
                    ContactMail = handler.contactmail()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.contactmail.__name__} Function failed', exc_info=True)
                    ContactMail = ''

                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                    Speakerlist = json.dumps(Speakerlist, ensure_ascii=False)
                    if Speakerlist is None:
                        Speakerlist = ''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_speakerlist.__name__} Function failed', exc_info=True)
                    Speakerlist = ''

                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if (venue or city):
                        online_event = 0
                    else:
                        online_event = 1
                except Exception as e:
                    error += '\n' + str(e)
                    online_event = ''

                data_row = [
                    scrappedUrl, eventname, startdate, enddate, timing,
                    eventinfo, ticketlist, orgProfile, orgName, orgWeb,
                    logo, sponsor, agendalist, type, category, city,
                    country, venue, event_website, googlePlaceUrl,
                    ContactMail, Speakerlist, online_event]

                GlobalFunctions.appendRow(file_name, data_row)

            except Exception as e:
                print(e)
                error += '\n' + str(e) + handler.error_msg_from_class
                logger.error('failed', exc_info=True)
                print('get here sometimes too')
                continue

except Exception as e:
    error += '\n' + str(e)
    logger.error('failed', exc_info=True)
    print(error)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)


# BYE!!!.

