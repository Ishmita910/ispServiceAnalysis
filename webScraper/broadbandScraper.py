import time
from . import ISP_Object
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
url = "https://broadbandnow.com/fastest-providers"

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


for item in soup.findAll('li', {"tbody"})[1:]:

    # create scraper object
    isp_object = ISP_Object()

    # hardcoded variable
    isp_object.website = 'FCC'
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
    t
            print(isp_object.print_data())

            # temp_df = str(isp_object.print_data())
            # temp_df=StringIO(temp_df)
            # df = pd.read_csv(temp_df, sep=",")
            # pd.DataFrame(df).to_csv('isp_object_out.csv',mode='a', index=False)

            # save data
            isp_object.save()
            #isp_object.write_csv()

driver.close()
