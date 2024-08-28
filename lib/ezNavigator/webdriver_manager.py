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
    
    def add_options(self) -> uc.ChromeOptions:   
        return uc.ChromeOptions()
    
    def get_driver(self, driverexe_path: Union[Path, str], chrome_options: uc.ChromeOptions, browser_logs: bool = False, performance_logs: bool = False) -> Optional[WebDriver]:
        driverexe_path = Path(driverexe_path) if isinstance(driverexe_path, str) else driverexe_path
        
        if driverexe_path.is_file():
            
            if performance_logs:
                chrome_options.set_capability(
                    "goog:loggingPrefs", {"performance": "ALL"}
                )
            
            if browser_logs:
                chrome_options.set_capability(
                    "goog:loggingPrefs", {"browser": "ALL"}
                )

            return uc.Chrome(chrome_options, driver_executable_path = str(driverexe_path))
        
    def search_by_element_or_null(self, driver: WebDriver, by: Literal['id', 'name', 'xpath', 'link_text', 'partial_link_text', 'tag_name', 'class_name', 'css_selector'], param: str, timeout: int = 10) -> Optional[WebElement]:
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
        
        try:
            element = WebDriverWait(driver, timeout).until(
                expected_conditions.presence_of_element_located(
                    (by, param)
                )
            )
            
            return element
            
        except(TimeoutException, NoSuchElementException, ):
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

    def search_by_image_or_null(self, image_paths: Union[str, List[str], Path, List[Path]], search_time: int, region: Optional[Tuple[int, int, int, int]] = None, confidence: float = 0.7, grayscale: bool = False) -> Optional[pyautogui.Point]:
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
        screenshot_bytes = driver.get_screenshot_as_png()
        
        screenshot_image = Image.open(io.BytesIO(screenshot_bytes))
        
        if region:
            screenshot_image = screenshot_image.crop(region)
        
        if download_path:
            download_path = os.path.join(download_path, filename)
        else:
            download_path = filename
            
        screenshot_image.save(download_path)
    
    def scroll_page(self, driver: WebDriver, direction: Literal['up', 'down'] = 'down', amount: int = 300) -> None:
        if direction == 'down':
            driver.execute_script(f"window.scrollBy(0, {amount});")
        elif direction == 'up':
            driver.execute_script(f"window.scrollBy(0, -{amount});")
    
    def execute_script(self, driver: WebDriver, script: str, *args) -> any:
        return driver.execute_script(script, *args)

    def get_console_logs(self, driver: WebDriver) -> List[Dict[str, str]]:
        if not self._check_capability(driver, "goog:loggingPrefs", {"browser": "ALL"}):
            raise RuntimeError("Driver was not configured to record console logs")

        try:
            logs = driver.get_log('browser')
            return logs
        
        except Exception:
            return []

    def get_local_storage(self, driver: WebDriver) -> dict:
        return driver.execute_script("return window.localStorage;")

    def set_local_storage(self, driver: WebDriver, key: str, value: str) -> None:
        driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
    
    def accept_alert(self, driver: WebDriver) -> None:
        try:
            WebDriverWait(driver, 10).until(expected_conditions.alert_is_present()).accept()
        except TimeoutException:
            print("No alert present")

    def dismiss_alert(self, driver: WebDriver) -> None:
        try:
            WebDriverWait(driver, 10).until(expected_conditions.alert_is_present()).dismiss()
        except TimeoutException:
            print("No alert present")

    def interact_with_popup(self, image_path: Union[str, Path], action: Literal['click', 'close'] = 'click', search_time: int = 10) -> bool:
        location = self.search_by_image_or_null(image_path, search_time)
        if location:
            if action == 'click':
                pyautogui.click(location)
            elif action == 'close':
                pyautogui.press('esc')
            return True
        return False

    def navigate_and_interact(self, driver: WebDriver, image_path: Union[str, Path], action: Literal['click', 'double_click'] = 'click', search_time: int = 10) -> bool:
        location = self.search_by_image_or_null(image_path, search_time)
        if location:
            if action == 'click':
                pyautogui.click(location)
            elif action == 'double_click':
                pyautogui.doubleClick(location)
            return True
        return False

    def _check_capability(self, driver: WebDriver, capability_name: str, expected_value) -> bool:
        return driver.capabilities.get(capability_name) == expected_value