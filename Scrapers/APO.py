from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import re
import dateutil.parser as dparser
import json
from utilities import string_clean
import os.path

def apo_scraper(sleep_period, previous_data=None):
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument('--headless')

	# Create browser driver object
	browser = webdriver.Chrome(options=chrome_options)
	browser.get('https://www.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/APO/')
	results_listing = browser.find_element_by_id('results-listing')

	main = BeautifulSoup(browser.page_source, "html.parser")
	results_to_loop = main.select('#results-listing li a')

	# Create dict to store info
	apo_decisions = {"decisions": []}

	# Loop through results listing
	for i in range(len(results_to_loop)):

		# Wait 200ms for DOM to load
		browser.implicitly_wait(200)
		# Necessary to abide by site scraping rules
		sleep(sleep_period)

		# Enter decision subpage
		links = browser.find_elements_by_xpath('/html/body/div[3]/div[1]/div[2]/ul/li')
		links[i].click()
		subpage = BeautifulSoup(browser.page_source, "html.parser")

		#
		# SCRAPING
		#

		# Title details
		title = subpage.title.text

		# Date details
		if (subpage.find_all(string=re.compile("Decision")) != []):
			date_text = subpage.find_all(string=re.compile("Decision"))[0].string
			datetime_raw = dparser.parse(date_text, fuzzy=True)
			date = datetime_raw.strftime('%d %B %Y')
			datetime = datetime_raw.strftime('%Y-%m-%d')
		else:
			print("Unable to retrieve date for: " + str(title))
			date = ""
			datetime = ""

		if (title == previous_data[0]) and (date == previous_data[1]):
			print("Reached last update")
			browser.quit()
			return apo_decisions

		else:
			# Patent details
			if (subpage.find_all(string=re.compile("Patent Application")) != []):
				patent_app = subpage.find_all(string=re.compile("Patent Application"))
				patent_app = re.findall('\d+', patent_app[0])[0]
			else:
				print("Unable to retrieve patent application details for: " + str(title))
				patent_app = ""

			# Applicant details
			if (subpage.find_all(string=re.compile("Patent Applicant")) != []):
				applicant = subpage.find_all(string=re.compile("Patent Applicant"))[0].string
				applicant = applicant.replace('Patent Applicant:\t', "")
			else:
				print("Unable to retrieve applicant details for: " + str(title))
				applicant = ""

			# Patent title
			if (subpage.find_all(string=re.compile("Title:\t")) != []):
				patent_title = subpage.find_all(string=re.compile("Title:\t"))[0].string
				patent_title = patent_title.replace("Title:\t", "").replace("\n", " ")
			else:
				print("Unable to retrieve patent title details for: " + str(title))
				patent_title = ""

			# Opponent details
			if (subpage.find_all(string=re.compile("Opponent:\t")) != []):
				opponent = subpage.find_all(string=re.compile("Opponent:\t"))[0].string
				opponent = opponent.replace("Opponent:\t", "").replace("\n", " ")
			else:
				print("Unable to retrieve opponent details for: " + str(title))
				opponent = ""

			# Delegate details
			if (subpage.find_all(string=re.compile("Delegate:\t")) != []):
				delegate = subpage.find_all(string=re.compile("Delegate:\t"))[0].string
				delegate = delegate.replace("Delegate:\t", "").replace('\n', ' ')
			else:
				print("Unable to retrieve delegate details for: " + str(title))
				delegate = ""

			# Applicant - patent attorney
			if (subpage.find_all(string=re.compile("Patent attorney for the applicant:", flags=re.I)) != []):
				applicant_pa = subpage.find_all(string=re.compile("Patent attorney for the applicant:", flags=re.I))[
					0].string
				applicant_pa = re.sub("\tPatent attorney for the applicant: ", "", applicant_pa, flags=re.I)
			else:
				print("Unable to retrieve applicant patent attorney details for: " + str(title))
				applicant_pa = ""

			# Applicant - counsel
			if (subpage.find_all(string=re.compile("Counsel for the applicant:", flags=re.I)) != []):
				applicant_counsel = subpage.find_all(string=re.compile("Counsel for the applicant:", flags=re.I))[
					0].string
				applicant_counsel = applicant_counsel.replace("Representation:\t", "")
				applicant_counsel = re.sub("Counsel for the applicant: ", "", applicant_counsel, flags=re.I)
			else:
				print("Unable to retrieve applicant counsel details for: " + str(title))
				applicant_counsel = ""

			# Opponent - patent attorney
			if (subpage.find_all(string=re.compile("Patent attorney for the opponent:", flags=re.I)) != []):
				opponent_pa = subpage.find_all(string=re.compile("Patent attorney for the opponent:", flags=re.I))[
					0].string
				opponent_pa = re.sub("\tPatent attorney for the opponent: ", "", opponent_pa, flags=re.I).replace("\n",
				                                                                                                  " ")
			else:
				print("Unable to retrieve opponent patent attorney details for: " + str(title))
				opponent_pa = ""

			# Opponent - counsel
			if (subpage.find_all(string=re.compile("Counsel for the opponent:", flags=re.I)) != []):
				opponent_counsel = subpage.find_all(string=re.compile("Counsel for the opponent:", flags=re.I))[
					0].string
				opponent_counsel = opponent_counsel.replace("Representation:\t", "").replace("\t", "")
				opponent_counsel = re.sub("Counsel for the opponent: ", "", opponent_counsel, flags=re.I)
			else:
				print("Unable to retrieve opponent counsel details for: " + str(title))
				opponent_counsel = ""

			# Construct decision dict object
			decision = {
				"title": title,
				"date": date,
				"datetime": datetime,
				"patent_application": patent_app,
				"patent_title": patent_title,
				"applicant": applicant,
				"opponent": opponent,
				"delegate": delegate,
				"applicant_pa": applicant_pa,
				"applicant_counsel": applicant_counsel,
				"opponent_pa": opponent_pa,
				"opponent_counsel": opponent_counsel
			}

			# Append decision to main dict
			apo_decisions["decisions"].append(decision)

			# Return to listings
			browser.execute_script("window.history.go(-1)")

	# Close browser driver
	browser.quit()
	print("APO scrape completed")

	# Return dict object containing scraped decisions
	return apo_decisions


def apo_scrape():

	if(os.path.isfile('../Data/apo.json')):
		# Load previous scrape data
		with open('../Data/apo.json', 'r') as apo_file:
			previous_data = json.load(apo_file)

		# Retrieve most recent decision from last update
		last_decision = [previous_data['decisions'][0]['title'], previous_data['decisions'][0]['date']]

		# Scrape
		APO_decisions = apo_scraper(1, previous_data=[last_decision[0], last_decision[1]])

		# Update file
		for i in range(len(previous_data['decisions'])):
			APO_decisions['decisions'].append(previous_data['decisions'][i])

		# Save file
		with open('../Data/apo.json', 'w', encoding='utf-8') as f:
			json.dump(APO_decisions, f, indent=4)

	else:
		# Scrape
		APO_decisions = apo_scraper(1, previous_data=[0,0])

		# Save file
		with open('../Data/apo.json', 'w', encoding='utf-8') as f:
			json.dump(APO_decisions, f, indent=4)