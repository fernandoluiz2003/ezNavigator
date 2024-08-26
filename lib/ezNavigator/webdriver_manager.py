from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions

import undetected_chromedriver as uc
from undetected_chromedriver.webelement import WebElement

from time import sleep

import json
import pyautogui

class WebDriverManager:
    
    def __init__(self):
        self.wait_time = 10
        
    def add_options(self) -> ChromeOptions:
        return uc.ChromeOptions()
    
    def get_driver(
        self, 
        driver_path: str = None, 
        chrome_options: ChromeOptions = None
    ) -> WebDriver: 
        
        if chrome_options is None:
            chrome_options = uc.ChromeOptions()
            
        chrome_options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL"}
        )
        
        return uc.Chrome(
            driver_executable_path =   driver_path,
            options                = chrome_options
        )
    
    def search_by_element(
        self, 
        driver: WebDriver,
        by    :       str, 
        param :       str,
        
        be_clickable: bool = False
    ) -> WebElement:
        
        by_mapping = {
            "id"               : By.ID,
            "name"             : By.NAME,
            "xpath"            : By.XPATH,
            "link_text"        : By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT,
            "tag_name"         : By.TAG_NAME,
            "class_name"       : By.CLASS_NAME,
            "css_selector"     : By.CSS_SELECTOR,
        }
        
        by = by_mapping.get(by.lower())
        
        if by is None:
            raise ValueError(f"Invalid locator type: {by}")
        
        if be_clickable == True:
            return WebDriverWait(
                driver  =        driver,
                timeout = self.wait_time
            ).until(
                expected_conditions.element_to_be_clickable(
                    (by, param)
                )
            )
            
        return WebDriverWait(
            driver  =        driver,
            timeout = self.wait_time
        ).until(
            expected_conditions.presence_of_element_located(
                (by, param)
            )
        )
    
    def change_frame(
        self,
        driver : WebDriver,
        by     : str= None,
        param  : str= None
    ):
        
        if not(by and param):
            driver.switch_to.default_content()
        
        else:
            driver.switch_to.frame(
                self.search_by_element(
                    driver, by, param
                )
            )
    
    def get_headers(
        self, 
        driver           :   WebDriver,
        headers_required : list = None,
        keys_required    : list = None,
        cookies_required : list = None
        
    ) -> dict | None:
        
        logs = driver.get_log('performace')
        
        for entry in logs:
            log = json.loads(entry['message'])['message']
            
            if log.get('method') == 'Network.requestWillBeSentExtraInfo':
                params = log.get('params', {})
                
                if keys_required and not all(key in params for key in keys_required):
                    continue
                
                headers = params.get('headers', {})
                
                if headers_required and not all(header in headers for header in headers_required):
                    continue
                
                cookies = headers.get('Cookie', '')
                if cookies_required and not all(cookie in cookies for cookie in cookies_required):
                    continue
                
                return headers
        
        return None

    def find_img(
        self,
        image_paths : str | list,
        search_time  : int,
        confidence : float = 0.7,
        grayscale  : bool = False
    ) -> tuple | None:
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        
        wait_time_image = 0
        while wait_time_image <= search_time:
            try:
                for image_path in image_paths:
                    locate_image = pyautogui.locateCenterOnScreen(
                        image = image_path,
                        grayscale = grayscale,
                        confidence = confidence
                    )
                    return locate_image
                    
            except Exception as e:
                pass
            
            finally:
                wait_time_image += 1
                sleep(1)
        
        return None