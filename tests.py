import unittest
from selenium import webdriver
from multiprocessing import Pool
import os
from pyvirtualdisplay import Display

display = Display(visible=0, size=(1024, 768))
display.start()

def runit(url):
    browser = webdriver.Firefox()
    browser.get(url)
 
    upload_input = browser.find_element_by_id('input_file')
    file_path = os.path.join(
        os.getcwd(), 
        'csv_example_messy_input.csv'
    )
    upload_input.send_keys(file_path)
    submit_button = browser.find_element_by_id('submit-upload')
    submit_button.click()
 
    for field in ['Source', 'Site name', 'Zip', 'Address']:
        browser.find_element_by_name(field).click()
    browser.find_element_by_id('start-training').click()

    for i in range(10):
        browser.find_element_by_id('yes').click()
        browser.find_element_by_id('no').click()
    browser.find_element_by_id('finish').click()

if __name__ == '__main__':
    pool = Pool(processes=10)
    for i in range(10):
        res = pool.apply_async(runit, ['http://dedupe.datamade.us'])
        print res.get()
