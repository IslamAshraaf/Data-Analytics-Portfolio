#THIS IS A (PLUS) CODE JUST TO SHOW SOME EXTRA SKILLS AND ANOTHER WAY TO SOLVE THE PROBLEM (NOT USED IN THE SCRIPT)
#The code dicover the data entry erros for the misspelling using google search
#--------------------------------------

#Libraries
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

#Code
def scrap(from_list,to_list):
    port_set = set(np.append(from_list,to_list))
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    browser = webdriver.Chrome(options=options)
    browser.maximize_window()
    #Open Website
    for port in port_set:
        browser.get(f'https://www.google.com/search?q={port} port')
        #Get correct name from did you mean by google
        try:
            correct_name = browser.find_element(By.ID,'fprsl').text
            print(f'Wrong Name : {port} --> Correction : {correct_name}')
        #Port name is correct
        except:
            continue
        
