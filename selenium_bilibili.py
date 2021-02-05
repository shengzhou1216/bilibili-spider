from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import TouchActions
from selenium.webdriver.firefox.options import Options

driver = webdriver.Firefox()
driver.get("https://www.bilibili.com/video/BV1EA411p7Jx")

wait_interval = 30
# 展开弹幕列表
zhankai = WebDriverWait(driver, wait_interval).until(
    EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'span.bui-collapse-arrow-text'))
)
zhankai.click()

# 弹幕容器
dm_container = WebDriverWait(driver, wait_interval).until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'ul.player-auxiliary-danmaku-list'))
)

dm_container_height = dm_container.size['height']

# 滚动条指示器
scroll_indicator = driver.find_element_by_css_selector('.bscroll-indicator')
print('scroll_indicator height: %d' % scroll_indicator.size['height'])
# 滚动条容器
scroll_bar_container=driver.find_element_by_css_selector(
    '.bscroll-vertical-scrollbar')
    
print('scroll_bar_container height: %d' % scroll_bar_container.size['height'])

scroll_bar_container_height=scroll_bar_container.size['height']

# 选中滚动条，向下拖动到底
webdriver.ActionChains(driver).click_and_hold(scroll_indicator).move_by_offset(
    0, scroll_bar_container.size['height']).perform()

# Perform release event
webdriver.ActionChains(driver).release().perform()

# 滚动弹幕容器
# driver.execute_script('arguments[0].scrollIntoView(true)', dm_container)

# 弹幕列表
dm_list=driver.find_elements_by_css_selector(
    'li.danmaku-info-row > span.danmaku-info-danmaku')

print(len(dm_list))

dms=[]
for dm_element in dm_list:
    dms.append(dm_element.text)

with open('dm.txt', 'w', encoding='utf8') as f:
    f.write(str(dms))
