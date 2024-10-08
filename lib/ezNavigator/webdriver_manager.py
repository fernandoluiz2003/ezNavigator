from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import undetected_chromedriver as uc
from undetected_chromedriver.webelement import WebElement

import pyautogui
from time import sleep

from pathlib import Path
from typing  import Union, Optional, Literal, List, Dict, Tuple

import os
import json

from PIL import Image
import io


class Manager:
    
    performance_logs_mode = False
    browser_logs_mode = False
    
    def add_options(self) -> uc.ChromeOptions: 
        """
        Returns ChromeOptions to configure the Chrome driver before instantiation.
        """  
        return uc.ChromeOptions()
    
    def get_driver(self, driverexe_path: Union[Path, str], chrome_options: uc.ChromeOptions, browser_logs: bool = False, performance_logs: bool = False) -> Optional[WebDriver]:   
        """
        Instantiates and returns a WebDriver object with optional logging capabilities.
        """
        driverexe_path = str(driverexe_path)
        
        if os.path.isfile(driverexe_path):
            
            if performance_logs is True:
                self.performance_logs_mode = True
                chrome_options.set_capability(
                    "goog:loggingPrefs", {"performance": "ALL"}
                )
            
            if browser_logs is True:
                self.browser_logs_mode = True
                chrome_options.set_capability(
                    "goog:loggingPrefs", {"browser": "ALL"}
                )

            return uc.Chrome(chrome_options, driver_executable_path = driverexe_path)
    
    def search_by_element(self, driver: WebDriver, by: Literal['id', 'name', 'xpath', 'link_text', 'partial_link_text', 'tag_name', 'class_name', 'css_selector'], param: str, timeout: int = 10) -> Optional[WebElement]:
        """
        Waits for and returns a WebElement located by a specified method (e.g., ID, XPath).
        """
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
        
        if by not in by_mapping:
            raise ValueError(f"Invalid locator type: {by}")
    
        by = by_mapping[by]
        
        element = WebDriverWait(driver, timeout).until(
            expected_conditions.presence_of_element_located(
                (by, param)
            )
        )
        
        return element

    def search_by_element_or_null(self, driver: WebDriver, by: Literal['id', 'name', 'xpath', 'link_text', 'partial_link_text', 'tag_name', 'class_name', 'css_selector'], param: str, timeout: int = 10) -> Optional[WebElement]:
        """
        Attempts to find a WebElement. Returns None if element is not found within the specified timeout.
        """
        try:
            element = self.search_by_element(driver, by, param, timeout)
            return element
            
        except(TimeoutException, NoSuchElementException, ):
            return None
        
    def change_iframe(self, driver: WebDriver, by: Optional[Literal['id', 'name', 'xpath', 'link_text', 'partial_link_text', 'tag_name', 'class_name', 'css_selector']] = None, param: Optional[str] = None) -> None:
        """
        Switches the WebDriver context to an iframe or back to the main content.
        """
        if by is None or param is None:
            driver.switch_to.default_content()
            return
        
        frame_element: WebElement = self.search_by_element_or_null(driver, by, param)
        driver.switch_to.frame(frame_element)
    
    def get_all_headers(self, driver: WebDriver, ignore: bool = False) -> Optional[List[Dict[str, str]]]:
        """
        Retrieves all headers from network logs recorded during the browser session.
        """
        if ignore == False:
            if self.performance_logs_mode == False:
                raise RuntimeError("Driver was not configured to record logs")

        list_headers = []
        
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
                headers = params.get('headers', {})
                list_headers.append(headers)

        return list_headers

    def search_by_image_or_null(self, image_paths: Union[str, List[str], Path, List[Path]], search_time: int, region: Optional[Tuple[int, int, int, int]] = None, confidence: float = 0.7, grayscale: bool = False) -> Optional[pyautogui.Point]:
        """
        Searches for an image on the screen within a specified time and returns its center coordinates if found.
        """
        if isinstance(image_paths, (str, Path)):
            image_paths = [Path(image_paths).as_posix()]
            
        elif isinstance(image_paths, list):
            image_paths = [Path(p).as_posix() if isinstance(p, (str, Path)) else p for p in image_paths]
    
        wait_time_image = 0
        while wait_time_image <= search_time:
            try:
                for image_path in image_paths:
                    
                    locate_image = pyautogui.locateCenterOnScreen(
                        image      = image_path,
                        region     =    region,
                        grayscale  = grayscale,
                        confidence = confidence
                    )
                    
                    return locate_image
                    
            except pyautogui.ImageNotFoundException:
                pass
            
            finally:
                wait_time_image += 1
                sleep(1)
        
        return None
    
    def capture_screenshot(self, driver: WebDriver, filename: str, download_path: Optional[str] = None, region: Optional[Tuple[int, int, int, int]] = None) -> None:
        """ 
        Captures a screenshot of the browser and saves it to the specified location.
        """
        screenshot = driver.get_screenshot_as_png()
        
        if region:
            screenshot_image = Image.open(io.BytesIO(screenshot))
            screenshot_image = screenshot_image.crop(region)
        else:
            screenshot_image = Image.open(io.BytesIO(screenshot))
        
        if download_path:
            if not filename.lower().endswith('.png'):
                filename += '.png'
            download_path = os.path.join(download_path, filename)
        else:
            if not filename.lower().endswith('.png'):
                filename += '.png'
            download_path = filename

        screenshot_image.save(download_path, format='PNG')
    
    def scroll_page(self, driver: WebDriver, direction: Literal['up', 'down'] = 'down', amount: int = 300) -> None:
        """
        Scrolls the page in the specified direction by a given amount.
        """
        if direction == 'down':
            driver.execute_script(f"window.scrollBy(0, {amount});")
        elif direction == 'up':
            driver.execute_script(f"window.scrollBy(0, -{amount});")
    
    def execute_script(self, driver: WebDriver, script: str, *args) -> any:
        """
        Executes a JavaScript script in the context of the browser.
        """
        return driver.execute_script(script, *args)

    def get_performance_logs(self, driver: WebDriver, ignore: bool = False) -> List[Dict[str, str]]:
        """
        Retrieves all performance logs generated during the browser session.
        """
        if ignore == False:
            if self.performance_logs_mode == False:
                raise RuntimeError("Driver was not configured to record console logs")

        try:
            logs = driver.get_log('performance')
            return logs
        
        except Exception:
            return []
    
    def get_console_logs(self, driver: WebDriver, ignore: bool = False) -> List[Dict[str, str]]:
        """
        Retrieves all console logs generated by the browser.
        """
        if ignore == False:
            if self.browser_logs_mode == False:
                raise RuntimeError("Driver was not configured to record console logs")

        try:
            logs = driver.get_log('browser')
            return logs
        
        except Exception:
            return []

    def get_local_storage(self, driver: WebDriver) -> dict:
        """
        Returns the contents of the browser's local storage.
        """
        return driver.execute_script("return window.localStorage;")

    def set_local_storage(self, driver: WebDriver, key: str, value: str) -> None:
        """
        Sets a key-value pair in the browser's local storage.
        """
        driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
    
    def accept_alert(self, driver: WebDriver) -> None:
        """
        Accepts a browser alert if one is present.
        """
        try:
            WebDriverWait(driver, 10).until(expected_conditions.alert_is_present()).accept()
        except TimeoutException:
            print("No alert present")

    def dismiss_alert(self, driver: WebDriver) -> None:
        """
        Dismisses a browser alert if one is present.
        """
        try:
            WebDriverWait(driver, 10).until(expected_conditions.alert_is_present()).dismiss()
        except TimeoutException:
            print("No alert present")

    def navigate_and_interact(self, image: Union[str, Path, pyautogui.Point], action: Literal['click', 'close', 'double_click'] = 'click', search_time: int = 10) -> bool:
        """
        Finds an image on the screen and performs an action on it (click, close, or double-click).
        """
        if isinstance(image, (str, Path)):
            location = self.search_by_image_or_null(image, search_time)
            
        elif isinstance(image, (pyautogui.Point, tuple)):
            location = image
            
        if location:
            if action == 'click':
                pyautogui.click(location)
            elif action == 'close':
                pyautogui.press('esc')
            elif action == 'double_click':
                pyautogui.doubleClick(location)
            return True
        return False

    def center_mouse_and_click(self, click_mouse: Optional[bool] = True) -> None:
        """
        Moves the mouse's cursor to the center of the screen
        """
        screen_width, screen_height = pyautogui.size()
        
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        pyautogui.moveTo(center_x, center_y)
        
        if click_mouse:
            pyautogui.click()
    
    def _check_capability(self, driver: WebDriver, capability_name: str, expected_value) -> bool:
        return driver.capabilities.get(capability_name) == expected_value