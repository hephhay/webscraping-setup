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
import regex

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

def date_tran(m, d, y):
    str_t = ' '.join((d,m,y))
    return datetime.strptime(str_t, '%d %b %Y').strftime('%Y-%m-%d')

def get_date_range(date_str):
    if date_str == '':
        return ('', '')
    date_match = re.search(r'([A-Za-z]{3})\s*(\d{0,2})\s*(?:\s*,\s*(\d{4})\s*)?.+?([A-Za-z]{3})?\s*(\d{0,2})\s*,.+?(\d{4})', date_str)
    date_g = date_match.groups()
    s_m, s_d, s_y, e_m, e_d, e_y = date_g
    if e_m == None:
        e_m = s_m
    if s_y == None:
        s_y = e_y
    prev = date_tran(s_m, s_d, s_y)
    end = date_tran(e_m, e_d, e_y)
    return (prev, end)

def get_price(price_s):
    if price_s == '':
        return ''
    p_s = price_s.split(' - ')
    return json.dumps(
        list(map(lambda x: {'type': 'paid', 'price': x[1:], 'currency': x[0]}, p_s)),
        ensure_ascii=False
    )

def f_time(time_s):
    if time_s == '':
        return ''
    t_r = re.search(r'(\d{1,2}(?:.\d{1,2})?\s*[AaMPm]{2})\s*.+?\s*(\d{1,2}(?:.\d{1,2})?\s*[aMPAm]{2})\s*([a-zA-Z]{2,3})', time_s)
    t_s, t_e, t_z = tuple(map(lambda x: x.replace(' ', ''), t_r.groups()))
    return json.dumps([{'type':'paid', 'start_time':t_s, 'end_time':t_e, 'timezone':t_z, 'days':'all'}], ensure_ascii = False)


def manipVals(val):
    val[1] = get_date_range(val[1])
    val[2] = get_price(val[2])
    val[3] = f_time(val[3])
    return val
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
    options.add_argument("--headless")
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
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
            except:
                pass
            try:
                all_url = [each.get_attribute('href') for each in self.dispatchList('.details>a')]
                all_title = [each.text for each in self.dispatchList('.details>a')]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return list(zip(all_url, all_title))

        def get_event(self, url: str) -> NoReturn:
            "Get a singualr event from a list of all events"
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
            
        
        
        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                page_prop = self.browser.execute_script("return "\
                "$('.details').map(function() {"\
                "child_list = $(this).children();"\
                "child_length = child_list.length;"\
                "switch (child_length) {"\
                "    case 3 :{"\
                "        info = document.evaluate('/html/body/main/section[1]/div/article/text()[3]', document, null, XPathResult.STRING_TYPE, null).stringValue.trim();"\
                "        date_str = '';"\
                "        price_str = $(child_list[1]).text();"\
                "        time_str = '';"\
                "        virtual = 1;"\
                "        venue = '';"\
                "        metro = '';"\
                "        break;"\
                "    }"\
                "    case 4 :{"\
                "        info = $('.article-detail p').first().text();"\
                "        date_str = $(child_list[0]).text();"\
                "        price_str = $(child_list[2]).text();"\
                "        time_str = $($(child_list[1]).children()[1]).html();"\
                "        virtual = 1;"\
                "        venue = '';"\
                "        metro = '';"\
                "        break;"\
                "    }"\
                "    case 5 :{"\
                "        info = $('.article-detail p').first().text();"\
                "        date_str = $(child_list[0]).text();"\
                "        price_str = $(child_list[3]).text();"\
                "        time_str = $($(child_list[1]).children()[1]).html();"\
                "        virtual = 1;"\
                "        venue = '';"\
                "        metro = '';"\
                "        break;"\
                "    }"\
                "    default :{"\
                "        info = $('.article-detail p').first().text();"\
                "        date_str = $(child_list[0]).text();"\
                "        price_str = $(child_list[4]).text();"\
                "        time_str = $($(child_list[1]).children()[1]).html();"\
                "        virtual = 0;"\
                "        venue = $(child_list[3]).text();"\
                "        metro = $(child_list[2]).text();"\
                "    }"\
                "}"\
                "return [[info, date_str, price_str, time_str, virtual, venue, metro]];"\
                "});"
                )
                page_prop = map(manipVals, page_prop)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return list(page_prop)

        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                price_t_1 = self.dispatch(".fusion-text tbody .row-1 .column-2").text
                price_v_1 = self.dispatch(".fusion-text tbody .row-2 .column-2").text.split(' ')
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
                    {'type':price_t_1, 'price':price_v_1[0], 'currency':price_v_1[1]}]

        def event_mode(self) -> List[str]:
            "Scrapes and return event venue "
            try:
                location = self.dispatch(".link-type-text>.content-container p").text.split('\n')
            except Exception as e:
                try:
                    location = self.dispatch("#slider-1-slide-1-layer-1").text.split(' | ')[1]
                except:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
                else:
                    return ['', '', location]
            else:
                return location
                    

        def contactmail(self) -> json:
            "Scrapes and return a JSONified format of event contact email(s)."
            try:
                soup = bs(self.browser.page_source,'lxml')
                rex=r"""(?:[a-z0-9!#$%&'+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'+/=?^_`{|}~-]+)|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])")@(?:(?:[a-z0-9](?:[a-z0-9-][a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-][a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
                ma=[regex.search(rex,fxc).group() for fxc in ' '.join(soup.body.get_text(separator=' ').split()).lower().split() if regex.search(rex,fxc) != None]
                mal=[dc[:-1] if dc.endswith('.') else dc for dc in ma]
                con = list(dict.fromkeys(mal+ ['CustomerRelations@theiia.org']))
                if con==[] or con=='':
                    con=['CustomerRelations@theiia.org']
            except:
                con = ['CustomerRelations@theiia.org']
            return con

        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                speaker_list = list(map(split_names, self.dispatchList('.fusion-one-fourth p[style="text-align: center;"]')))
                speaker_list = speaker_list[1:]
                if speaker_list == []:
                    raise IndexError
            except Exception as e:
                try:
                    speaker_list = list(map(split_names, self.dispatchList('.bklyn-team-member-info')))
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
                else:
                    return list(map(lambda a: {'name':a[0], 'title': a[1], 'link': ''}, speaker_list))
            else:
                return list(map(lambda a: {'name':a[0], 'title': a[1], 'link': ''}, speaker_list))

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


    base_url = 'https://www.theiia.org/en/search/course-search/?page=1&rpp=500'

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

            # if i[0] == 'https://insightevents.se/events/battery-tech-for-ev/':
            #     continue
            try:
                try:
                    handler.get_event(i[0])
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
                scrappedInfo = handler.event_info()
                for line_data in scrappedInfo:
                    try:
                        startdate = line_data[1][0]
                        enddate = line_data[1][0]
                    except Exception as e:
                        error += '\n' + str(e)
                        logger.error(f'{handler.event_date.__name__} Function failed', exc_info=True)
                        startdate = ''
                        enddate = ''
                    
                
                    # 5 BLOCK CODE: scraping attribute timing
                    try:
                        timing = line_data[3]
                    except Exception as e:
                        error += '\n' + str(e)
                        logger.error(f'{handler.event_timing.__name__} Function failed', exc_info=True)
                        timing = ''


                    # 6 BLOCK CODE: scraping attribute event_info
                    try:
                        eventinfo = line_data[0].strip().replace('\n', ' ')
                        if not eventinfo:
                            eventinfo = f'Theme: {eventname.title()} + {startdate} - {enddate}'
                    except Exception as e:
                        error += '\n' + str(e)
                        logger.error(f'{handler.event_info.__name__} Function failed', exc_info=True)
                        eventinfo = ''


                    # 7 BLOCK CODE: scraping attribute ticketlist
                    try:
                        ticketlist = line_data[2]
                        if ticketlist:
                            pass
                        else: ticketlist = ''
                    except Exception as e:
                        error += '\n' + str(e)
                        logger.error(f'{handler.event_ticket_list.__name__} Function failed', exc_info=True)
                        ticketlist = ''

                    # 8 BLOCK CODE: scraping attribute orgProfile
                    orgProfile = "Established in 1941, The Institute of Internal Auditors (IIA) is an international professional association with global headquarters in Lake Mary, Florida, USA. The IIA is the internal audit profession's leader in standards, certification, education, research, and technical guidance throughout the world. Generally, members work in internal auditing, risk management, governance, internal control, information technology audit, education, and security."

                    # 9 BLOCK CODE: scraping attribute orgName
                    orgName = 'theiia'

                    # 10 BLOCK CODE: scraping attribute orgWeb
                    orgWeb = 'https://www.theiia.org/en/'

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
                        mode = ''
                    except Exception as e:
                        error += '\n' + str(e)
                        logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)

                    # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                    try:
                        venue = line_data[5]
                        city = line_data[6]
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
                        Speakerlist = '[]'
                        if Speakerlist is None:
                            Speakerlist = ''
                    except Exception as e:
                        error += '\n' + str(e)
                        logger.error(f'{handler.event_speakerlist.__name__} Function failed', exc_info=True)
                        Speakerlist = ''

                    # 23 BLOCK CODE: scraping attribute online_event
                    online_event = line_data[4]

                    data_row = [
                        scrappedUrl, eventname, startdate, enddate, timing,
                        eventinfo, ticketlist, orgProfile, orgName, orgWeb,
                        logo, sponsor, agendalist, type, category, city,
                        country, venue, event_website, googlePlaceUrl,
                        ContactMail, Speakerlist, online_event]

                    GlobalFunctions.appendRow(file_name, data_row)

            except Exception as e:
                error += '\n' + str(e) + handler.error_msg_from_class
                logger.error('failed', exc_info=True)
                continue

except Exception as e:
    error += '\n' + str(e)
    logger.error('failed', exc_info=True)
    print(error)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)


# BYE!!!.

