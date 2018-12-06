from datetime import datetime
import csv

class DSL_Object(object):
    # All the scraper variables and their default value
    success = True
    def __init__(self, date = datetime.now().strftime("%Y-%m-%d"),
                    datetime = datetime.now().strftime("%H:%M:%S"),
                    website = None, source_url = None,
                    plan_name = None, plan_brand = None, is_reseller = None,
                    # is_contract = None, contract_length_months = None, download_speed = None,
                    # upfront_cost = None, upfront_promotion = None ,signal_price = None,
                    average_monthly_cost = None, monthly_total_contract_cost = None, total_cost_of_ownership = None):

        self.date = date
        self.datetime = datetime
        self.website = website
        self.source_url = source_url
        self.plan_name = plan_name
        self.plan_brand = plan_brand
        self.is_reseller = is_reseller

        self.average_monthly_cost = average_monthly_cost
        self.monthly_total_contract_cost = monthly_total_contract_cost

        self.total_cost_of_ownership = total_cost_of_ownership



    # Use this function to print the data
    def print_data(self):
        data = {
            "Date":self.date,
            "Datetime":self.datetime,
            "Website":self.website,
            "Source url":self.source_url,
            "Plan Name":self.plan_name,
            "Plan Brand":self.plan_brand,
            "Is Reseller":self.is_reseller,

            "Average Monthly Cost":self.average_monthly_cost,
            "Monthly Total Contract Cost":self.monthly_total_contract_cost,

            "Total Cost of Ownership":self.total_cost_of_ownership,

        return data

    # Save the data to the database
    def save(self):
        print("save")

    def write_csv(self):
        with open('preis24.csv', 'a', newline='') as csvfile:
            filewriter = csv.writer(csvfile)
            filewriter.writerow([self.date,
                                self.datetime,
                                self.website,
                                self.source_url,
                                self.plan_name,
                                self.plan_brand,
                                self.is_reseller,

                                self.average_monthly_cost,
                                self.monthly_total_contract_cost,

                                self.total_cost_of_ownership])

