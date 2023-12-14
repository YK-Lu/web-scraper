import pandas as pd
import os
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_directory(dir_name):
    # 檢查目錄是否存在，不存在則創建
    if not os.path.exists(dir_name):
        print(f"保存數據的目錄 {dir_name} 不存在，已創建 {dir_name}")
        os.makedirs(dir_name)
    else:
        print("目錄已存在")

def start_browser():
     # 啟動瀏覽器並設置選項
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=zh-TW")
    return webdriver.Chrome(options=options)

def open_google_maps(driver):
    # 開啟Google地圖
    driver.get("https://www.google.com/maps")
    time.sleep(5)

def search_and_select_store(driver, store_name):
    # 在Google地圖中搜尋並選擇指定店家
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.clear()
    search_box.send_keys(store_name)
    time.sleep(2)  # 等待頁面加載

    # 判斷第一個建議是否存在
    first_suggestion = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div#cell0x0 span.cGyruf.fontBodyMedium.RYaupb > span"))
    )
    # 選擇第一個建議
    first_suggestion.click()
    time.sleep(2)  # 等待頁面加載

def scroll_and_expand_reviews(driver):
    # 滾動並展開評論
    actions = ActionChains(driver)
    scrollable_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]")))
    
    no_change_counter = 0
    prev_reviews = 0
    while True:
        reviews = driver.find_elements(By.XPATH, "//span[@class='wiI7pd']")
        if len(reviews) >= 400 or no_change_counter >= 7:
            break

        if len(reviews) == prev_reviews:
            no_change_counter += 1
        else:
            no_change_counter = 0
        prev_reviews = len(reviews)

        for _ in range(10):
            scrollable_element.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.07)

    # 展開所有評論
    for button in driver.find_elements(By.CSS_SELECTOR, "button.w8nwRe.kyuRq"):
        try:
            button.click()
        except Exception as e:
            print(f"Could not click on button: {str(e)}")
        time.sleep(1)

def extract_and_save_reviews(driver, store_name, df, csv_file_path):
    # 提取並保存評論
    reviews = driver.find_elements(By.XPATH, "//span[@class='wiI7pd']")
    stars = driver.find_elements(By.XPATH, "//span[@class='kvMYJc']")
    for i, (review_element, star_element) in enumerate(zip(reviews, stars)):
        review_text = review_element.text.strip()
        star_text = star_element.get_attribute("aria-label").strip()

        if len(review_text) > 5:
            code = df.loc[df['名稱'] == store_name, 'Code'].values[0]
            store_name = df.loc[df['名稱'] == store_name, '名稱'].values[0]

            with open(csv_file_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([code, store_name, review_text, star_text])

def main():
    # 主程序
    comment_save_dir = './comment'
    create_directory(comment_save_dir)

    df = pd.read_csv('./a_1.csv')
    store_names = df['名稱'].iloc[0:4000]
    driver = start_browser()
    open_google_maps(driver)

    csv_file_path = os.path.join(comment_save_dir, "店家評論資訊.csv")
    completed_keywords_file = '已爬暫存區.txt'
    completed_keywords = set()

    # 讀取已完成的關鍵詞
    if os.path.exists(completed_keywords_file):
        with open(completed_keywords_file, 'r') as file:
            for line in file:
                completed_keywords.add(line.strip())

    for store_name in store_names:
        if store_name in completed_keywords:
            print(f"關鍵字 {store_name} 已經爬取過，跳過")
            continue
        else:
            try:
                search_and_select_store(driver, store_name)
                scroll_and_expand_reviews(driver)
                extract_and_save_reviews(driver, store_name, df, csv_file_path)

                completed_keywords.add(store_name)
                with open(completed_keywords_file, 'a') as file:
                    file.write(store_name + '\n')

            except Exception as e:
                print(f"跳過 {store_name}，出現錯誤: {e}")

    driver.quit()

if __name__ == "__main__":
    main()