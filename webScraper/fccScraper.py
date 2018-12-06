import time
# from ISP_Object import ISP_Object
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver import FirefoxOptions
import os
import pandas as pd
# import

opts = FirefoxOptions()
# opts = Options()
opts.add_argument("--headless")

# To clear the old content
filename = "isp_object_out.csv"
# opening the file with w+ mode truncates the file
f = open(filename, "w+")
f.close()

def parse_money(string):
    string = string.strip()
    string = string[:-2]
    string = string.split("\\")[0]
    string = string.replace(',', '.')
    string = string.replace('\\xa0', ' ')
    return string

driver = webdriver.Firefox(firefox_options=opts)
driver.implicitly_wait(5)


# new connection, minimum speed of 6000, flat internet selected
url = "https://www.fcc.gov/reports-research/reports/measuring-broadband-america/measuring-fixed-broadband-report-2016"

# get url
driver.get(url)
time.sleep(5)

# load all the options on the page
show_more = True
while show_more:
    try:
        show_more_button = driver.find_element_by_class_name("cms_continiuer-elem")
        show_more_button.location_once_scrolled_into_view
        show_more_button.click()
        time.sleep(5)
    except NoSuchElementException:
        show_more = False

# get soup
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
# get ID
# driver.entertext <key word>
# X path
# iterate over each offer, skipping first one
for item in soup.findAll('li', {'itemtype': 'http://schema.org/Product'})[1:]:

    # create scraper object
    isp_object = ISP_Object()

    # hardcoded variable
    isp_object.website = 'Preis 24'
    isp_object.is_reseller = True
    isp_object.is_contract = True
    isp_object.contract_length_months = 24
    isp_object.upfront_promotion = 0
    isp_object.data_included = 999
    isp_object.is_converged_tv_option = False
    isp_object.is_converged_mobile_option = False

    # time-determined variables
    isp_object.date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    isp_object.datetime = datetime.now(timezone.utc).strftime("%H:%M:%S")

    # visible data on preview of offer
    isp_object.plan_brand = item.find("div", {"class": "cms-widget_calculator_result_list_provider-name"}).text
    isp_object.plan_name = item.find("div", {"class": "cms-widget_calculator_result_list_offer_name"}).text
    isp_object.download_speed = item.find("div", {"data-vic": "arrow-down-2"}).text.split(" ")[0]

    # source url (link on button or link for page if sold out)
    try:
        source_url = "https://www.preis24.de" + item.find("a", {"class": "cms_button"})["href"]
    except TypeError:
        source_url = url
    isp_object.source_url = source_url

    # not all options have tv
    try:
        tv_included = item.find("div", {"data-vic": "tv"}).contents[0].strip()
        if tv_included.find('TV inklusive') != -1:
            isp_object.is_converged_tv_included = True
        else:
            isp_object.is_converged_tv_included = False
    except AttributeError:
        isp_object.is_converged_tv_included = False

    # bullet points (landline and mobile)
    bullets = item.find("li", {"class", "cms-widget_calculator_result_list_remarks-flex"})
    if not bullets.findAll("li", {"data-vic": "check"}):
        isp_object.is_converged_landline_included = False
    for check in bullets.findAll("li", {"data-vic": "check"}):
        if check.contents[0].find("Inkl. Festnetz-Flat") != -1:
            isp_object.is_converged_landline_included = True
            break
        elif check.contents[0].find("Inkl. Allnet-Flat") != -1 \
                or check.contents[0].find("Inkl. Telefon-Flat in alle Netze") != -1:
            isp_object.is_converged_landline_included = True
            isp_object.is_converged_mobile_included = True
            isp_object.mobile_voice_data = 999
            break
        else:
            isp_object.is_converged_landline_included = False

    # warning bullet (throttling)
    warning = bullets.find("li", {"data-vic": "warning-2"})
    try:
        warning = warning.text.strip().lower()
        isp_object.is_throttle = True
        if warning.find("kbit/s") != -1:
            throttle_speed = warning.split("kbit/s")[-2]
            throttle_speed = throttle_speed.strip()
            throttle_speed = throttle_speed.split(' ')[-1]
            isp_object.throttle_speed = throttle_speed
        if warning.find('drosselung ab 300 gb') != -1:
            isp_object.data_included = 300
        elif warning.find('drosselung ab 100 gb') != -1:
            isp_object.data_included = 100
        elif warning.find('gb pro') != -1:
            data_volume = warning.split("gb pro")[0]
            data_volume = data_volume.strip()
            data_volume = data_volume.split(" ")[-1]
            isp_object.data_included = data_volume
        elif warning.find('gb/monat') != -1:
            data_volume = warning.split("gb/monat")[0]
            data_volume = data_volume.strip()
            data_volume = data_volume.split(" ")[-1]
            isp_object.data_included = data_volume
    except AttributeError:
        isp_object.is_throttle = False

    # create signal price list
    signal_price_list = []

    # parse through tables to get contract length, hardware, prices
    all_tables = item.find("div", {"data-tab-handle": "1"}).findAll("div", recursive=False)
    # parse(table_1_text_rows)

    # price table
    table_1_text_rows = all_tables[0].find("tbody").findAll('tr')
    for row in table_1_text_rows[1:-1]:
        columns = row.findAll('td')
        if "Gesamtkosten" in columns[0].text:
            isp_object.upfront_cost = "{:.2f}".format(float(parse_money(columns[2].text)))
            isp_object.average_monthly_cost = "{:.2f}".format(float(parse_money(columns[1].text)) / float(24))
            isp_object.monthly_total_contract_cost = "{:.2f}".format(float(isp_object.average_monthly_cost) * float(24))
        elif columns[0].text == 'Durchschnittspreis pro Monat':
            isp_object.monthly_total_contract_cost = "{:.2f}".format(float(isp_object.average_monthly_cost) * float(24))
        elif columns[1].text != '' and columns[0].text.find("1.") != -1:
            signal_price_list.append(parse_money(columns[1].text))

    # compile first month prices from signal price list
    isp_object.signal_price = float(0.00)
    for price in signal_price_list:
        isp_object.signal_price = float(isp_object.signal_price) + float(price)
    isp_object.signal_price = "{:.2f}".format(float(isp_object.signal_price))

    # contract table
    table_3_text_rows = all_tables[1].find("tbody").findAll("tr")
    min_contract = table_3_text_rows[0].findAll("td")
    if "Mindest" in min_contract[0].text:
        if min_contract[1].text.find("Monate") != -1:
            isp_object.contract_length_months = int(min_contract[1].text.replace("Monate", "").strip())
        else:
            isp_object.contract_length_months = 0
    if isp_object.contract_length_months == 0:
        isp_object.is_contract = False

    # additional options (possibly converged mobile)
    if not isp_object.is_converged_mobile_included:
        isp_object.is_converged_mobile_included = False
        try:
            for extras in all_tables[3].find("tbody").findAll("tr")[1:]:
                extras_row = extras.findAll("td")
                if extras_row[0].text in converged_mobile:
                    isp_object.is_converged_mobile_option = True
                    isp_object.mobile_voice_data = 999
                    if extras_row[1].text.find("Monat") != -1:
                        isp_object.converged_mobile_monthly_cost = "{:.2f}".format(float(extras_row[1].text[:-7].replace(',', '.')))
                    break
                else:
                    # set converged_mobile none entries to False
                    isp_object.is_converged_mobile_included = False
        except (IndexError, AttributeError):
            # set converged_mobile none entries to False
            isp_object.is_converged_mobile_included = False

    # hardware table
    # if there is no hardware options set device options to None and save to db
    if not all_tables[2].find("tbody"):
        isp_object.is_modem_bundle = False
        isp_object.device_name = None
        isp_object.device_brand = None
        isp_object.device_monthly_cost = None

        isp_object.total_cost_of_ownership = "{:.2f}".format((float(isp_object.average_monthly_cost) * float(24) + float(isp_object.upfront_cost)))
        isp_object.monthly_bundle_contract_cost = "{:.2f}".format((float(isp_object.average_monthly_cost) * float(24) + float(isp_object.upfront_cost)))

        # print(isp_object.print_data())
        # save data
        isp_object.save()
        #isp_object.write_csv()
        continue

    # if there is hardware option, iterate through hardware options & create row for each hardware option
    else:
        isp_object.is_modem_bundle = True
        for hardware in all_tables[2].find("tbody").findAll("tr")[1:]:
            hardware_row = hardware.findAll("td")
            isp_object.device_name = hardware_row[0].text

            # device brand
            if hardware_row[0].text.find("Fritz") != -1 or hardware_row[0].text.find("FRITZ") != -1:
                isp_object.device_brand = "FRITZ!Box"
            else:
                isp_object.device_brand = isp_object.plan_brand

            # device option and cost
            if hardware_row[3].text.find("*") != -1:
                isp_object.device_monthly_cost = 0
                isp_object.is_options = False
            else:
                isp_object.is_options = True
                if hardware_row[3].text.find("kostenlos") != -1:
                    isp_object.device_monthly_cost = 0
                elif hardware_row[3].text.find("einmalig") != -1:
                    isp_object.device_monthly_cost = "{:.2f}".format((float(hardware_row[3].text[:-11].replace(',', '.')))/float(24))
                else:
                    isp_object.device_monthly_cost = hardware_row[3].text[:-8].replace(',', '.')
            # print("device monthly cost"+isp_object.device_monthly_cost+"end")
            # print("monthly contract cost" + isp_object.monthly_total_contract_cost + "end")
            isp_object.total_cost_of_ownership = "{:.2f}".format((float(isp_object.average_monthly_cost) * float(24) + float(isp_object.device_monthly_cost))*float(24))
            isp_object.monthly_bundle_contract_cost = "{:.2f}".format(float(isp_object.average_monthly_cost) * float(24) + float(isp_object.device_monthly_cost))


            print(isp_object.print_data())

            # temp_df = str(isp_object.print_data())
            # temp_df=StringIO(temp_df)
            # df = pd.read_csv(temp_df, sep=",")
            # pd.DataFrame(df).to_csv('isp_object_out.csv',mode='a', index=False)

            # save data
            isp_object.save()
            #isp_object.write_csv()

driver.close()
