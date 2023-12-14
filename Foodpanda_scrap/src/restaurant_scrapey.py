from fake_useragent import UserAgent
import requests
from bs4 import BeautifulSoup as bs
import random
import time
import os
import csv





## 檢查要放資料的目錄是否存在
def scrape_restaurants():
    save_dir = './res_data'
    if not os.path.exists(save_dir):
        print(f"放檔案的 {save_dir} 目錄不在，已建立{save_dir}")
        os.makedirs(save_dir)
    else:
        print("res_data目錄已存在，將開始爬蟲")

    all_restaurants = []
    page = 1

#主要爬蟲迴圈，直到not res_info
    while True:
        try:
            # 目標網址，使用變量 'page' 來控制頁面
            url = f"https://www.foodpanda.com.tw/city/changhua?page={page}"
            # 生成隨機的用戶代理以模擬瀏覽器行為
            headers = {'User-Agent': UserAgent().random}

            # 發送請求並獲取網頁內容
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'

            # 使用 BeautifulSoup 的 lxml 解析器解析網頁內容
            soup = bs(response.text, "lxml")

            # 使用 CSS 選擇器查找頁面中的特定元素，這裡尋找的是包含餐廳信息的 'figcaption' 標籤
            res_info = soup.find_all('figcaption', {'class': 'vendor-info'})
            # 如果找不到任何餐廳信息，則跳出迴圈
            if not res_info:
                    break
            
            # 遍歷每一個包含餐廳信息的 'figcaption' 元素
            for res in res_info:
                # 從每個 'figcaption' 元素中找到餐廳名稱
                res_name = res.find('span', {'class': 'name fn'})
                # 從 'figcaption' 的父元素（通常是 'a' 標籤）中找到餐廳網址
                res_url = res.find_parent('a')['href']
                # 從每個 'figcaption' 元素中找到餐廳評分
                res_rating = res.find('span', {'class': 'ratings-component'})
                # 從每個 'figcaption' 元素中找到餐點類型
                res_type = res.find('li', {'class': 'vendor-characteristic'})  

                # 檢查並提取每個元素的文本，如果元素不存在則標記為 "未知"
                res_name_text = res_name.text if res_name else "未知"
                res_url_text = res_url if res_url else "未知"
                res_rating_text = res_rating.get('aria-label', '未知') if res_rating else "未知"
                res_type_text = res_type.text if res_type else "未知"

                # 將提取的單個餐廳資料作為字典添加到列表 'all_restaurants' 中
                restaurant = {
                    '名稱': res_name_text,
                    '網址': res_url_text,
                    '評分': res_rating_text,
                    '餐點類型': res_type_text
                }
                all_restaurants.append(restaurant)
                
            # 完成當前頁面的爬蟲後，輸出進度信息並進入下一頁，隨機休息30到120秒以避免被網站封鎖
            print(f"已完成第{page}頁的爬蟲。")
            page += 1

            #隨機休息30-120秒
            time.sleep(random.uniform(30, 120))
        except Exception as e:  
            # 如果在爬蟲過程中遇到任何異常，則打印錯誤信息並停止迴圈
            print(f"爬蟲出現錯誤: {e}")
            break
    city_name = url.split("/")[-1].split("?")[0]
    return all_restaurants, save_dir, city_name

# 寫入CSV文件
def save_to_csv(all_restaurants, save_dir, city_name):
    print("正在寫入檔案...")
    try:
        # 構建CSV文件的完整路徑
        csv_file_path = os.path.join(save_dir, f"{city_name}.csv")

        # 打開CSV文件準備寫入。使用 'utf-8-sig' 
        with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            # 定義CSV文件的列標題
            fieldnames = ['名稱', '網址', '評分', '餐點類型']
            # 創建一個DictWriter實例，用於寫入字典形式的數據
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # 寫入列標題
            writer.writeheader()
            # 遍歷列表中的所有餐廳數據，並逐行寫入CSV文件
            for restaurant in all_restaurants:
                writer.writerow(restaurant)
        # 寫入成功後輸出提示信息
        print(f"{city_name}地區CSV儲存成功，腳本已結束")

    except Exception as e:
        # 捕捉並處理寫入CSV時可能出現的異常
        print(f"儲存{city_name}的CSV時發生錯誤: {e}")

if __name__ == "__main__":
    all_restaurants, save_dir, city_name = scrape_restaurants()
    save_to_csv(all_restaurants, save_dir, city_name)