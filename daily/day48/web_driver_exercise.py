from selenium import webdriver

from tools.consts import CHROME_DRIVER_PATH


def gamestop_signin():
    SITE = "https://www.gamestop.com/video-games/playstation-5/consoles/products/playstation-5/11108140.html"
    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH)
    driver.get(SITE)
    print(driver.title)
    my_account = driver.find_element_by_css_selector("a.d-none")
    my_account.click()
    sign_in = driver.find_element_by_link_text("SIGN IN")
    sign_in.click()
    login_email = driver.find_element_by_id("login-form-email")
    login_email.clear()
    login_email.send_keys("abc123456@gmail.com")

    login_email = driver.find_element_by_id("login-form-password")
    login_email.clear()
    login_email.send_keys("abc123456")

    sign_in = driver.find_element_by_css_selector("#signinCheck button.btn")
    sign_in.click()

    time.sleep(10)
    driver.close()


def cookie_clicker():
    COOKIE_SITE = "http://orteil.dashnet.org/experiments/cookie/"
    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH)
    driver.get(COOKIE_SITE)
    print(driver.title)
    driver.find_element_by_id("toggleNumbers").click()
    driver.find_element_by_id("toggleFlash").click()

    cookie = driver.find_element_by_css_selector("div#cookie")
    store = driver.find_element_by_css_selector("div#store")
    clicked = 0
    while clicked < 100:
        cookie.click()
        clicked += 1

    driver.find_element_by_css_selector("div#exportSave.button").click()
    alert = driver.switch_to_alert()  # DOES NOT WORK WITH PYTHON!!!!!!!!!!! AUHHHH
    # ^alert prompt text input is inaccessible
    print(alert.text)

    driver.close()
