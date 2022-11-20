# -*- coding: utf-8 -*-
"""
@author: ChewingGumKing_OJF
"""
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

#loads necessary libraries
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

#*******************************************************************************************************************
sys.path.insert(
    0,
    os.path.dirname(__file__).replace('parsing-new-script', 'global-files/'))

import json
#*******************************************************************************************************************
import warnings

import requests
from GlobalFunctions import *
from GlobalVariable import *

warnings.filterwarnings("ignore")

try:
    file_name = sys.argv[1]  #file name from arguments (1st)
    port = int(sys.argv[2])  #port number from arguments (2nd)

    GlobalFunctions.createFile(
        file_name)  #to created TSV file with header line

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    path = GlobalVariable.ChromeDriverPath
    driver = webdriver.Chrome(options=options, executable_path=path, port=port)

    error: str = ''

    @dataclass
    class ScrapeEvent:
        """ the codebase design uses a Class with it Methods as function scraping singular data(some more,
        in the case of going inside the page just once). It returns the data to a it caller which is handled by a context manager"""

        browser: WebDriver = driver
        wait_5sec: WebDriverWait = WebDriverWait(browser, 5)
        error_msg_from_class: str = '' 

        def __enter__(self):
            return self

        def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
            self.browser.quit()

        def all_scrapped_url(self, link: str) -> list:
            """  loads and scrapes all event urls"""

            container = []
            self.browser.get(link)

            flag = True
            while flag:
                time.sleep(1.5)
                urls = self.browser.find_elements(By.LINK_TEXT, 'To event')
                all_urls = [i.get_attribute('href') for i in urls]
                try:
                    next_page = self.wait_5sec.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.pagination-next-pages a')))
                    next_page.click()
                except NoSuchElementException or TimeoutException: 
                    container += all_urls
                    flag = False
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    container += all_urls
                    flag = False
                else:
                    container += all_urls
                    flag = True
            
            return container


        def get_event(self, url: str) -> None:
            self.browser.get(url)


        def event_name(self) -> str:
            try:
                sc_event_name = self.browser.find_element(
                    By.CSS_SELECTOR, '.documentFirstHeading').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return sc_event_name


        def event_date(self) -> tuple:
            try:
                sc_event_date = self.browser.find_element(
                    By.CSS_SELECTOR, '.event-page .date').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:

                def _date_tranf(date_data: str) -> tuple:
                    """ refines the date_data to required format"""

                    if '\n' in date_data:
                        date_data = date_data.replace('\n', '')

                    if ';' in date_data: # 'Nov 10, 2023; Course of talks'
                        raw = date_data.split(';')[0]

                        if '-' in raw:  # 'Jan 10, 2023 - Nov 10, 2023; Course of talks'
                            date_data = ''.join(raw)
                            _raw = date_data.split('-')
                            start =  datetime.strptime(
                            _raw[0].strip(), '%b %d, %Y').strftime('%Y-%m-%d')
                            end =  datetime.strptime(
                            _raw[1].strip(), '%b %d, %Y').strftime('%Y-%m-%d')
                            return start, end

                        rf_raw = datetime.strptime(
                            raw, '%b %d, %Y').strftime('%Y-%m-%d')
                        return rf_raw, rf_raw
                    elif ';' not in date_data:
                        rf_raw = datetime.strptime(
                            date_data, '%b %d, %Y').strftime('%Y-%m-%d')
                        return rf_raw, rf_raw
                    else:
                        pass

                if sc_event_date:
                    rf_event_date = _date_tranf(sc_event_date)
                    return rf_event_date
                else:
                    return '', ''


        def event_timing(self) -> json:
            """ refines the time_data to required format"""
            try:
                sc_event_time = self.browser.find_element(
                    By.CSS_SELECTOR, '.time').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:

                def _time_tranf(time_data: str) -> str:
                    if '\n' in time_data:
                        time_data = time_data.replace('\n', '')

                    if 'all-day' in time_data:
                        return None

                    if not time_data or  time_data == '' or time_data == ' ' or time_data == '  ':
                        return None

                    if '-' in time_data:  #'04:40 PM - 06:10 PM'
                        start_time, end_time = time_data.split(
                            '-')[0].strip().replace(
                                ' ',
                                ''), time_data.split('-')[1].strip().replace(
                                    ' ', '')


                        if ',' in start_time:  # 'Jan 10, 2023, 06:30 PM - Nov 10, 2023, 08:00 PM'
                            start_time = start_time.split(',')[2]
                        if ',' in end_time:
                            end_time = end_time.split(',')[2]

                        return start_time, end_time
                    else:
                        start_time, end_time = time_data.strip().replace(
                            ' ', ''), ''
                        return start_time, end_time

                if sc_event_time:
                    rf_event_time = _time_tranf(sc_event_time)
                    if rf_event_time:
                        return [
                            json.dumps(
                                dict(type='general',
                                    Start_time=rf_event_time[0],
                                    end_time=rf_event_time[1],
                                    timezone='',
                                    days='all'))
                        ]
                    else:
                        return ''
                else:
                    return ''

        def event_info(self) -> str:
            try:
                sc_event_info = self.browser.find_element(
                    By.CSS_SELECTOR, '.event-page .date').text
                if ';' in sc_event_info:
                    raw = sc_event_info.split(';')[1]
                    return raw
                else:
                    return ''
            except Exception as e:
                self.error_msg_from_class += '\n' + e

        
        def event_ticket_list(self) -> json:
            try:
                soup = bs(self.browser.page_source,'html.parser')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                all_text = ' '.join(soup.body.text.split())
                ticket = re.search(r'Fee:\s*([\w,]+)\s*(Euro|Pound|Dollar|€|£|$|)', all_text)   # "/p{Sc}" for regexep for currency sybmols gives error
                if ticket:
                    fee, currency = ticket.group(1), ticket.group(2)

                    if str(fee).lower() == 'free':
                        return json.dumps({'type':'free', 'price':'free', 'currency':''})
                    if currency is None:
                        currency = ''
                    
                    fee = fee.replace(',', '.')

                    _ticket_list = json.dumps({'type':'paid', 'price':f'{fee}', 'currency':f'{currency}'}, ensure_ascii=False)
                    return _ticket_list
                else:
                    return ''
                

        def event_location(self) -> str:
            try:
                sc_event_location2 = self.browser.find_element(
                By.CSS_SELECTOR, '.address').text
            except NoSuchElementException:
                sc_event_location2 = ' '   # This field is less common
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                sc_event_location2 = ' '

            try:
                sc_event_location = self.browser.find_element(
                    By.CSS_SELECTOR, '.location').text
            except NoSuchElementException:
                pass
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                sc_event_location += sc_event_location2
                if '\n' in sc_event_location:
                    sc_event_location = sc_event_location.replace('\n', '')

                loc = "The location can be found on the internal webpage."

                if 'Zoom' in sc_event_location or loc in sc_event_location or 'Online' in sc_event_location or 'online' in sc_event_location or 'digital' in sc_event_location:
                    return 'ONLINE'
                else:
                    return sc_event_location


        def google_map_url(self, search_word) -> str:
            """ this implementation of the Google serach function is neccesary because of the nature of the website"""
            if search_word == 'ONLINE':
                return 'ONLINE'

            curr_tab = self.browser.current_window_handle
            self.browser.switch_to.new_window('tab')

            try:
                def gu(luc):
                    google_url_for_location="https://www.google.com/search?q="+luc+"&oq="+luc+"&num=1"
                    time.sleep(randint(0,3))
                    driver.get(google_url_for_location)
                    time.sleep(4)
                    try:
                        google_map_url=driver.find_element("id",'lu_map').click()
                    except:
                        try:
                            google_map_url=driver.find_element("class name",'Xm7sWb').click()
                        except:
                            try:
                                google_map_url=driver.find_element("class name",'dirs').click()
                            except:
                                try:
                                    google_map_url=driver.find_element("class name",'GosL7d cYnjBd').click()
                                except:
                                    google_map_url=driver.find_element("class name",'Lx2b0d').click()
                    time.sleep(1)
                    google_map_url=driver.current_url
#                 print(google_map_url)
                    return(google_map_url)
        ######################################
                def get_google_map_url(location):
                    try:
                        return(gu(location))
                    except:
                        try:
                            return(gu(location))
                        except:
                            sha=location.split(',')
                            try:
                                return(gu(sha[-3]))
                            except:
                                try:
                                    return(gu(sha[-2]))
                                except:
                                    try:
                                        return(gu(sha[-1]))
                                    except Exception as e:
                                        print(location, "; url didn't go through")
                                        print(e)
                                        return("")
                map_url = get_google_map_url(search_word)
            except Exception as e:
                error = '\n\n' + str(e)
            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url                


        def event_speakerlist(self):
            try:
                sc_event_speakerlist = self.browser.find_element(
                    By.CSS_SELECTOR, '.speaker').text
            except NoSuchElementException:
                return ''
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                container = []
                if '\n' in sc_event_speakerlist:
                    sc_event_speakerlist = sc_event_speakerlist.strip().split('\n')

                    for i in sc_event_speakerlist:
                        if i == "":
                            continue
                        
                        if ',' in i:
                            _name = i.split(',')[0]
                            _link = i.split(',')[1]
                            
                            if len(i.split(',')) == 3:

                                _name = i.split(',')[0] + i.split(',')[1]
                                _link = i.split(',')[2]
                            
                            temp_use = dict(name=_name, title='', link=_link)
                        else:
                            temp_use = dict(name=i, title='', link='')
                            
                        container.append(
                            json.dumps(temp_use.copy(), ensure_ascii=False))
                else:  # if only a value is present
                    if ',' in sc_event_speakerlist:
                        _name = sc_event_speakerlist.split(',')[0]
                        _link = sc_event_speakerlist.split(',')[1]

                        if 'selected newly appointed professors' in _name:
                            return ''
                            
                        if 'http' in _link:
                            _link = ''
                            
                        if len(sc_event_speakerlist.split(',')) == 3:

                            _name = sc_event_speakerlist.split(',')[0] + sc_event_speakerlist.split(',')[1]
                            _link = sc_event_speakerlist.split(',')[2]
                                
                        temp_use = dict(name=_name, title='', link=_link)
                    else:
                        temp_use = dict(name=sc_event_speakerlist,
                                    title='',
                                    link='')
                                    
                    container.append(
                        json.dumps(temp_use.copy(), ensure_ascii=False))
            return container
                    


        def event_contact_mail(self) -> list:
            try:
                soup = bs(self.browser.page_source,'html.parser')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                all_text = ' '.join(soup.body.text.split())
                emails = re.findall(r'[\w\.-]+@[\w\.-]+', all_text)
                if emails:
                    return json.dumps(emails, ensure_ascii=False)
                else:
                    return json.dumps(['servicecenter.studium@tu-dresden.de', 'infostelle@tu-dresden.de', 'pressestelle@tu-dresden.de'])


    base_url = 'https://tu-dresden.de/tu-dresden/veranstaltungskalender/veranstaltungskalender'

    with ScrapeEvent() as handler:
        """ This context manager handles the ScrapeEvent() Class object and instantiates it caller varaibles"""
        handler.browser.implicitly_wait(5)
        #flagx: int = 1  # helps to check when NO more event with next_page() function
        #while flagx < 3:
            # your code for getting the links of events page from list page and storing them in a list

        try:
            links = handler.all_scrapped_url(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
    # end of first part

    # second part
        for link in links:
            try:
                """ checks if url is valid/not broken """
                valid_url = requests.get(link)
                if valid_url.status_code < 400:
                    # 1 BLOCK CODE: scraping attribute scrappedUrl
                    scrappedUrl = link
                    """ GET THE EVENT"""
                    try:
                        handler.get_event(scrappedUrl)
                    except Exception as e:
                        error += '\n' + str(e)
                else:
                    continue

                # 2 BLOCK CODE: scraping attribute eventtitle
                try:
                    sc_name = handler.event_name()
                    eventname = sc_name
                except Exception as e:
                    error += '\n' + str(e)
                    eventname = ''

                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    sc_date = handler.event_date()
                    startdate = sc_date[0]
                    enddate = sc_date[1]
                except Exception as e:
                    error += '\n' + str(e)
                    startdate = ''
                    enddate = ''

                # 5 BLOCK CODE: scraping attribute timing
                try:
                    timing = handler.event_timing()
                except Exception as e:
                    error += '\n' + str(e)
                    timing = ''

                # 6 BLOCK CODE: scraping attribute event_info
                try:
                    eventinfo = handler.event_info()
                    if eventinfo:
                        eventinfo = str(eventinfo).upper() + ': ' + str(
                            eventname).lower()
                    else:
                        eventinfo = f'{eventname.lower()}  starting by {startdate.lower()} and ending {enddate.lower()}'
                except Exception as e:
                    error += '\n' + str(e)
                    eventinfo = ''

                # 7 BLOCK CODE: scraping attribute ticketlist
                try:
                    ticketlist = handler.event_ticket_list()
                except Exception as e:
                    error += '\n' + str(e)
                    ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'Technische Universität Dresden is an effective partner for local, national and global collaborations in research, teaching and transfer.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'Technische Universität Dresden'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://tu-dresden.de/'

                # 11 BLOCK CODE: scraping attribute logo
                logo = ''

                # 12 BLOCK CODE: scraping attribute sponsor
                #sponsor = handler.event_sponsor(index)
                sponsor = ''

                # 13 BLOCK CODE: scraping attribute agendalist
                agendalist = ''

                #14 BLOCK CODE: scraping attribute type
                type = ''
                #15 BLOCK CODE: scraping attribute category
                category = ''

                # 16 BLOCK CODE: scraping attribute city
                try:
                    sc_city = handler.event_location()
                    if sc_city == 'ONLINE':
                        city = ''
                    else:
                        if len(sc_city) < 20:
                            city = sc_city
                        else:
                            city = ''
                except Exception as e:
                    error += '\n' + str(e)
                    city = ''


                # 18 BLOCK CODE: scraping attribute venuev
                try:
                    sc_venue = handler.event_location()
                    if sc_venue == 'ONLINE':
                        venue = ''
                    else:
                        if len(sc_venue) > 20:
                            venue = sc_venue
                        else:
                            venue = ''
                except Exception as e:
                    error += '\n' + str(e)
                    venue = ''

                # 17 BLOCK CODE: scraping attribute country
                if city or venue:
                    country = 'Germany'
                else:
                    country = ''

                # 19 BLOCK CODE: scraping attribute event_website
                event_website = scrappedUrl

                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if venue == '' or not venue:
                        googlePlaceUrl = ''
                    else:
                        sc_search_word = f'{venue} {city} {country}'
                        gg_map = handler.google_map_url(sc_search_word)
                        googlePlaceUrl = gg_map
                except Exception as e:
                    error += '\n' + str(e)
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                try:
                    sc_ContactMail = handler.event_contact_mail()
                    ContactMail = sc_ContactMail
                except Exception as e:
                    error += '\n' + str(e)
                    ContactMail = ''


                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                except Exception as e:
                    error += '\n' + str(e)
                    Speakerlist = ''

                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if sc_venue == 'ONLINE':
                        online_event = 1
                    else:
                        online_event = 0
                except Exception as e:
                    error += '\n' + str(e)
                    online_event = ''

                data_row = [
                    scrappedUrl, eventname, startdate, enddate, timing,
                    eventinfo, ticketlist, orgProfile, orgName, orgWeb,
                    logo, sponsor, agendalist, type, category, city,
                    country, venue, event_website, googlePlaceUrl,
                    ContactMail, Speakerlist, online_event
                ]
                GlobalFunctions.appendRow(file_name, data_row)

            except Exception as e:
                print(e)
                error += '\n' + str(e) + handler.error_msg_from_class
                continue

except Exception as e:
    error += '\n' + str(e)
    print(e)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)
 