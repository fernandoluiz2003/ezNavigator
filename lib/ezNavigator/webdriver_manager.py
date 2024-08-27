from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

import undetected_chromedriver as uc
from undetected_chromedriver.webelement import WebElement

from pyautogui import locateCenterOnScreen
from time import sleep

from pathlib import Path
from typing  import Union, Optional, Literal, List, Dict, Tuple

import json

class Manager:
    
    def add_options(self) -> ChromeOptions:   
        return uc.ChromeOptions()
    
    def get_driver(self, driverexe_path: Union[Path, str], chrome_options: ChromeOptions, performance_logs: bool = False) -> Optional[WebDriver]:
        
        try: 
            driverexe_path = Path(driverexe_path) if isinstance(driverexe_path, str) else driverexe_path
            
            if driverexe_path.is_file():
                
                if performance_logs:
                    chrome_options.set_capability(
                        "goog:loggingPrefs", {"performance": "ALL"}
                    )

                return uc.Chrome(chrome_options, driver_executable_path = driverexe_path)
        
        finally:
            return None
        
    def search_by_element_or_null(self, driver: WebDriver, by: Literal['id', 'name', 'xpath', 'link_text', 'partial_link_text', 'tag_name', 'class_name', 'css_selector'], param: str, timeout: int) -> Optional[WebElement]:
        by_mapping = {
            "id"               : By.ID,
            "name"             : By.NAME,
            "xpath"            : By.XPATH,
            "tag_name"         : By.TAG_NAME,
            "link_text"        : By.LINK_TEXT,
            "class_name"       : By.CLASS_NAME,
            "css_selector"     : By.CSS_SELECTOR,
            "partial_link_text": By.PARTIAL_LINK_TEXT,
        }
        
        by = by_mapping.get(by.lower(), None)
        
        if by is None:
            raise ValueError(f"Invalid locator type: {by}")
        
        try:
            return WebDriverWait(driver, timeout).until(
                expected_conditions.presence_of_element_located(
                    (by, param)
                )
            )
            
        except TimeoutException:
            return None
        
    def change_iframe(self, driver: WebDriver, by: Optional[Literal['id', 'name', 'xpath', 'link_text', 'partial_link_text', 'tag_name', 'class_name', 'css_selector']] = None, param: Optional[str] = None) -> None:
        if by is None or param is None:
            driver.switch_to.default_content()
            return
        
        frame_element: WebElement = self.search_by_element_or_null(driver, by, param)
        driver.switch_to.frame(frame_element)
    
    def get_headers(self, driver: WebDriver, headers_required: Optional[List[str]] = None, keys_required: Optional[List[str]] = None, cookies_required: Optional[List[str]] = None) -> Optional[Dict[str, str]]:
        if not self._check_capability(driver, "goog:loggingPrefs", {"performance": "ALL"}):
            raise RuntimeError("Driver was not configured to record logs")

        try:
            logs = driver.get_log('performance')
            
        except Exception:
            return None

        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                
            except (KeyError, json.JSONDecodeError):
                continue

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

    def search_by_image_or_null(self, image_paths: Union[str, List[str], Path, List[Path]], search_time: int, confidence: float = 0.7, grayscale: bool = False) -> Optional[Tuple[int, int]]:
        if isinstance(image_paths, (str, Path)):
            image_paths = [Path(image_paths).as_posix()]
            
        elif isinstance(image_paths, list):
            image_paths = [Path(p).as_posix() if isinstance(p, (str, Path)) else p for p in image_paths]
    
        wait_time_image = 0
        while wait_time_image <= search_time:
            try:
                for image_path in image_paths:
                    
                    locate_image = locateCenterOnScreen(
                        image      = image_path,
                        grayscale  = grayscale,
                        confidence = confidence
                    )
                    
                    return locate_image
                    
            except Exception:
                pass
            
            finally:
                wait_time_image += 1
                sleep(1)
        
        return None
        
    def _check_capability(self, driver: WebDriver, capability_name: str, expected_value) -> bool:
        return driver.capabilities.get(capability_name) == expected_value