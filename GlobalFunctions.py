import sys
import os
import csv
import time
import re
import json
from datetime import date
from random import randint
from datetime import datetime, timedelta
import requests
sys.path.insert(0, os.path.dirname(__file__).replace('global-files','global-files/'))
from GlobalVariable import *

class GlobalFunctions:
	def createFile(file_name):
		with open(GlobalVariable.TsvFilePath+file_name+'.tsv', 'wt') as csvfile:
			tsv_writer = csv.writer(csvfile, delimiter='\t')
			tsv_writer.writerow(['scrappedUrl', 'eventname', 'startdate', 'enddate','timing', 'eventinfo', 'ticketlist', 'orgProfile', 'orgname', 'orgweb', 'logo', 'sposor', 'agendalist', 'type', 'category', 'city', 'country', 'venue', 'event_website', 'googlePlaceUrl', 'ContactMail', 'Speakerlist', 'online_event'])
                

	def appendRow(file_name, row_data):
		with open(GlobalVariable.TsvFilePath+file_name+'.tsv', 'a+', encoding="utf-8", newline='') as out_file:
			tsv_writer = csv.writer(out_file, delimiter='\t')
			tsv_writer.writerow(row_data)

	def update_scrpping_execution_status(file_name, error):
		print("done")

	def get_google_map_url(location, driver):
		try:
			google_url_for_location="https://www.google.com/search?q="+location+"&oq="+location+"&num=1"
			driver.get(google_url_for_location)
			time.sleep(randint(0,3))
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
			time.sleep(2)
			google_map_url=driver.current_url
			return(google_map_url)
		except Exception as e:
			# print(e)
			return("")

	def date_converter(dat):
		if dat.startswith('-'):
			dat=dat[1:]
		dat=dat.replace('&','-').replace(' and ',' - ').replace('ugust','u-g-u-s-t').replace('st','').replace('u-g-u-s-t','ugust').replace('turday','t-u-r-d-a-y').replace('rd','').replace('t-u-r-d-a-y','turday').replace('th','').replace('nday','n-d-a-y').replace('nd','').replace('n-d-a-y','nday').title()

		if any (ele in dat for ele in [date(2000, 5, d).strftime('%a') for d in range(1, 8)]):    
			da=dat.split('-')
			datt=[]
			for d in da:
				for f in re.findall('[A-Za-z]+',d):
					for o in ([date(2000, 5, d).strftime('%a') for d in range(1, 8)]):
						if o in f:
							rit=d.replace(f,'').replace('–','').strip().replace('  ',' ')
							datt.append(rit)
			if len(datt)==1:
				datt=[datt[0],datt[0]]

			dat=datt[0]+' - '+datt[1]
		else:
			pass
		dat=dat.replace('–','-').replace('|','').replace('to','-').replace('TO','-').strip().replace('c-ber','ctober').replace('C-BER','CTOBER')
		if '(' in dat:
			dat=dat.split('(')[0].strip()     
		if dat=='':
			start_date=end_date=''
		else:

			mad=dat

			if '-' in mad:
				st=mad.split('-')[0].strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()
				en=mad.split('-')[1].strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()

			elif 'and'in mad:
				st=mad.split('and')[0].strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()
				en=mad.split('and')[1].strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()

			elif '&' in mad:
				st=mad.split('&')[0].strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()
				en=mad.split('&')[1].strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()

			else:
				st=mad.strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()
				en=mad.strip().replace(',','').replace('nd','').replace('st','').replace('th','').replace('rd','').replace('ugu','ugust').strip()

			
				#                 08.09. - 09.09.2022(day,month)dat
			if re.search('\d{1,2}\.+\s?\d{1,2}\.?\s?\-\s?\d{1,2}\.?\d{1,2}\.?\d{4}',mad.strip()):
				#                 print(mad,'kiy')
				start=mad.split('-')[0].split('.')[0].strip()+' '+datetime.strptime(mad.split('-')[0].split('.')[1].strip(), '%m').strftime('%B')+' '+mad.split('-')[1].split('.')[2].strip()
				end=mad.split('-')[1].split('.')[0].strip()+' '+datetime.strptime(mad.split('-')[1].split('.')[1].strip(), '%m').strftime('%B')+' '+mad.split('-')[1].split('.')[2].strip()

				
				#                 08. - 09.09.2022(day)dat
			elif re.search('\d{1,2}\.?\s?\-\s?\d{1,2}\.?\d{1,2}\.?\d{4}',mad.strip()):
				#                 print(mad,'act')

				start=mad.split('-')[0].split('.')[0].strip()+' '+datetime.strptime(mad.split('-')[1].split('.')[1].strip(), '%m').strftime('%B')+' '+mad.split('-')[1].split('.')[2].strip()
				end=mad.split('-')[1].split('.')[0].strip()+' '+datetime.strptime(mad.split('-')[1].split('.')[1].strip(), '%m').strftime('%B')+' '+mad.split('-')[1].split('.')[2].strip()

				#                 09.09.2022(single)dat
			elif re.search('\d{1,2}\.+\s?\d{1,2}\.?\s?\d{4}',mad.strip()):
				#                 print(mad,'suat')

				start=end=mad.split('.')[0].strip()+' '+datetime.strptime(mad.split('.')[1].strip(), '%m').strftime('%B')+' '+mad.split('.')[2].strip()
				
			
			elif any(c.isalpha() for c in st)==False:
				#                 print('leg')
				pa=re.search('[A-Sa-z]+\W+(\d{4})',en)#, maxsplit=0)
				sapa=pa.group()
				start=st+' '+sapa
				end=en
				#                        02        April      2022
			elif re.search('\d{1,2}\s+[A-Sa-z]{3,9}\s\d{4}',st):
				#                 print('awujale')
				start=st
				end=en
				#             2022 Aug 25(st,en)
			elif re.search('\d{4}\s+[A-Sa-z]{3,9}\s\d{1,2}',st):
				#                 print('caus')
				pa=re.search('(\d{4})',st).group()
				sa=re.search('([A-Sa-z]{3,9})',st).group()
				ta=re.findall('(\d{1,2})',st)[-1]
				start=ta+' '+sa+' '+pa
				#
				ba=re.search('(\d{4})',en).group()
				ca=re.search('([A-Sa-z]{3,9})',en).group()
				da=re.findall('(\d{1,2})',en)[-1]
				end=da+' '+ca+' '+ba

				#*                        April       02      2022
			elif re.search('[A-Sa-z]{3,9}\s\d{1,2}\s+\d{4}',st):
				#                 print('ala')
				pa=re.search('(\d{4})',st).group()
				sa=re.search('([A-Sa-z]{3,9})',st).group()
				ta=re.search('(\d{1,2})',st).group()
				start=ta+' '+sa+' '+pa
				#
				ba=re.search('(\d{4})',en).group()
				ca=re.search('([A-Sa-z]{3,9})',en).group()
				da=re.search('(\d{1,2})',en).group()
				end=da+' '+ca+' '+ba

				#                 June 15 - September 30, 2022'
			elif re.search('[A-Sa-z]{3,9}\s+\d{1,2}',st) and re.search('[A-Sa-z]{3,9}\s\d{1,2}\s+\d{4}',en):
				ba=re.search('(\d{4})',en).group()
				ca=re.search('([A-Sa-z]{3,9})',en).group()
				da=re.search('(\d{1,2})',en).group()
				end=da+' '+ca+' '+ba
				sa=re.search('([A-Sa-z]{3,9})',st).group()
				ta=re.search('(\d{1,2})',st).group()
				start=ta+' '+sa+' '+ba

				#                      02     2022
			elif re.search('\d{1,2}\s+\d{4}',en):
				#      print('kum')
				pa=re.search('(\d{4})',en).group()#, maxsplit=0)
				sa=re.search('([A-Sa-z]{3,9})',st).group()
				ta=re.search('(\d{1,2})',st).group()

				start=ta+' '+sa+' '+pa
				#
				ba=re.search('(\d{4})',en).group()
				ca=re.search('([A-Sa-z]{3,9})',st).group()
				da=re.search('(\d{1,2})',en).group()
				end=da+' '+ca+' '+ba

				#	                      02         April
			elif re.search('\d{1,2}\s+[A-Sa-z]{3,9}',st):
				#        print('is')
				pa=re.search('(\d{4})',en)#, maxsplit=0)
				sapa=pa.group()
				start=st+' '+sapa
				end=en
			
				#*                      April           02
			elif re.search('[A-Sa-z]{3,9}\s+\d{1,2}',st):
				#      print('bad')
				pa=re.search('(\d{4})',en).group()#, maxsplit=0)
				sa=re.search('([A-Sa-z]{3,9})',st).group()
				ta=re.search('(\d{1,2})',st).group()

				start=ta+' '+sa+' '+pa
				#
				ba=re.search('(\d{4})',en).group()
				ca=re.search('([A-Sa-z]{3,9})',en).group()
				da=re.search('(\d{1,2})',en).group()
				end=da+' '+ca+' '+ba

			else:
				#     print('shik')
				start=end=''
			if start=='':
				start_date=end_date=''
			else:
				pick=[start, end]
				try:
					spl_dt_obj = [datetime.strptime(v, '%d %B %Y') for v in pick]
				except:
					spl_dt_obj = [datetime.strptime(v, '%d %b %Y') for v in pick]
				date_= [z.strftime('%Y-%m-%d') for z in spl_dt_obj]
				start_date=date_[0]
				end_date=date_[1]
				if start_date>end_date:
					start_date=str(eval(start_date.split('-',1)[0])-1)+'-'+str(start_date.split('-',1)[-1])
		return (start_date,end_date)

		

	def price_converter(prices):
		"""takes in a list of strings containing the prices as input. Examples of the forms it can process are 
		['60 USD for children','type: USD 5','participants: 800INR',"oleggggggg : free","Advance Prices|Adult: 7$","Advance Prices|Senior Citizen / Registered Disabled:6£"]
			"""
		if prices==[] or prices=='':
			ticket_list=''
		else:
			ticket=[]
			for price in prices:
				try:
					if not regex.search(r"\p{Sc}",price) and not re.search('[A-Z]{3}',price) and not ':' in price and 'ree' not in price:
						pass
					else:
						if ':' not in price and not 'ree' in price:
							ty='paid'
							try:
								cu=re.search("\\$|\\£|\\€|\\USD|\\EUR|\\GBP",price).group()
							except:
								try:
									cu=regex.search(r"\p{Sc}",price).group()
								except:
									try:
										cu=re.search('[A-Z]{3}',price).group()
									except:
										cu=''
							am=re.search('\d+\.?\d*',price.split(':')[-1].replace(',','').replace(' ','')).group()

						elif ':' not in price and 'ree' in price:
							ty='free'
							am=''
							cu=''
							
						elif price=='Free'or price=='free' or 'Free' in price or 'free' in price:
							cu=''
							am='0'
							ty=price.split(':')[0].strip().replace(am,'').replace(cu,'').strip()
							if len(ty)<4:
								ty='free'
								
						elif regex.search(r"\p{Sc}\W*\d+",price):
							try:
								cu=regex.search(r'\p{Sc}',price).group()
							except:
								cu=''
							am=regex.search('\d+\.?\d*',price.split(':')[-1].replace(',','').replace(' ','')).group()
							ty=price.split(':')[0].strip().replace(am,'').replace(cu,'').strip()

							if len(ty)<4:
								ty='paid'
								
						elif re.search("\\$\W*\d+|\\£\W*\d+|\\€\W*\d+",price):
							try:
								cu=re.search("\\$|\\£|\\€",price).group()
							except:
								cu=''
							am=re.search('\d+\.?\d*',price.split(':')[-1].replace(',','').replace(' ','')).group()
							ty=price.split(':')[0].strip().replace(am,'').replace(cu,'').strip()

							if len(ty)<4:
								ty='paid'
								

						elif re.search("\\USD|\\EUR|\\GBP",price):
							try:
								cu=re.search("\\USD|\\EUR|\\GBP",price).group()
							except:
								cu=''
							am=re.search('\d+\.?\d*',price.split(':')[-1].replace(',','').replace(' ','')).group()
							ty=price.split(':')[0].strip().replace(am,'').replace(cu,'').strip()
							
							if len(ty)<4:
								ty='paid'
								
						elif re.search('[A-Z]{3}',price):
							try:
								cu=re.search('[A-Z]{3}',price).group()
							except:
								cu=''
							am=re.search('\d+\.?\d*',price.split(':')[-1].replace(',','').replace(' ','')).group()

							ty=price.split(':')[0].strip().replace(am,'').replace(cu,'').strip()
							if len(ty)<4:
								ty='paid'

						elif re.search('\d+',price):
							cu='$'
							am=re.search('\d+\.?\d*',price.replace(',','').replace(' ','')).group()
							ty=price.split(':')[0].strip().replace(am,'').replace(cu,'').strip()
							if len(ty)<4:
								ty='paid'

						else:
							ty='free'
							cu=''
							am=''

						tic={
							'type':ty,
							'price':am,
							'currency':cu
						}
						ticket.append(tic)
				except:
					continue
			
			ticket_list=json.dumps(ticket,ensure_ascii=False)
			if ticket==[]:
				ticket_list=''
		return ticket_list
