import os
import time
import csv
import requests
import pandas as pd
import pickle
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor 

# 建立所需的目錄
def create_directories():
    directories = ['./food_img', './error', './backup', './crawled_vendors']
    for dir in directories:
        if not os.path.exists(dir):
            os.makedirs(dir)
            print(f"建立{dir}目錄")

# 讀取店家ID
def read_vendor_ids(file_path):
    df = pd.read_csv(file_path)
    return df.iloc[:, 0]

# 讀取已經爬取的店家ID
def read_crawled_vendors(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return set(f.read().splitlines())
    return set()

# 從FOODPANDA的API獲取店家數據
def fetch_vendor_data(vendor_id, headers):
    url = f"https://tw.fd-api.com/api/v5/vendors/{vendor_id}?include=menus"
    response = requests.get(url, headers=headers)
    return response.json()

# 下載圖片
def download_image(image_info):
    file_path, img_filename, headers = image_info
    if not file_path.startswith('http://') and not file_path.startswith('https://'):
        # 如果URL無效，跳過下載
        return
    try:
        img_response = requests.get(file_path, headers=headers)
        img_filepath = f"./food_img/{img_filename}"
        with open(img_filepath, 'wb') as img_file:
            img_file.write(img_response.content)
    except Exception as e:
        pass

# 保存備份數據
def save_backup(data, vendor_id):
    with open(f'./backup/dishes_info_backup_{vendor_id}.pkl', 'wb') as backup_file:
        pickle.dump(data, backup_file)

# 記錄已爬取的供應商ID
def append_crawled_vendor(file_path, vendor_id):
    with open(file_path, 'a') as f:
        f.write(f"{vendor_id}\n")

# 記錄錯誤店家
def log_error(file_path, vendor_id, e):
    with open(file_path, 'a') as error_file:
        error_file.write(f"{vendor_id}\n")
    print(f"Error with vendor_id {vendor_id}: {e}")

# 寫入CSV檔案
def write_to_csv(file_path, data):
    with open(file_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
        csvwriter = csv.writer(csvfile)
        for row in data:
            csvwriter.writerow(row)

# 處理餐點數據
def process_vendor_data(vendor_id, vendor_data, headers):
    img_urls = []
    dishes_info = []

    # 獲取店家地址、經緯度、菜單類別等信息
    address = vendor_data.get('address', '')
    latitude = vendor_data.get('latitude', '')
    longitude = vendor_data.get('longitude', '')
    cuisines = ",".join([cuisine['name'] for cuisine in vendor_data.get('cuisines', [])])

    for menu in vendor_data.get('menus', []):
        for category in menu.get('menu_categories', []):
            for product in category.get('products', []):
                # 圖片命名規則：vendor_id + product_id
                img_filename = f"{vendor_id}_{product['id']}.jpg"
                img_url = product.get('file_path', '')
                
                # 跳過無效的圖片URL
                if not img_url.startswith(('http://', 'https://')):
                    continue

                # 獲取餐點價格
                product_variations = product.get('product_variations', [])
                price = product_variations[0].get('price', '') if product_variations else ''

                # 添加圖片下載任務
                img_urls.append((img_url, img_filename, headers))

                # 保存餐點信息
                dishes_info.append([
                    img_filename, product['name'], product['id'], product['description'],
                    address, latitude, longitude, cuisines, price
                ])
    # 使用ThreadPoolExecutor進行多線程下載圖片
    with ThreadPoolExecutor() as executor:
        executor.map(download_image, img_urls)

    return dishes_info

# 估計剩餘時間
def estimate_remaining_time(vendor_index, total_vendors, total_dishes, product_crawl_times, past_vendor_product_counts):
    estimated_remaining_vendors = total_vendors - (vendor_index + 1)

    # 計算平均每個供應商的餐點數
    if past_vendor_product_counts:
        average_products_per_vendor = sum(past_vendor_product_counts) / len(past_vendor_product_counts)
    else:
        average_products_per_vendor = 0

    # 估計剩餘的餐點數
    estimated_remaining_dishes = estimated_remaining_vendors * average_products_per_vendor

    # 計算平均爬取時間
    if product_crawl_times:
        average_crawl_time = sum(product_crawl_times) / len(product_crawl_times)
    else:
        average_crawl_time = 0

    # 估計剩餘時間
    estimated_time = average_crawl_time * estimated_remaining_dishes
    hours, remainder = divmod(estimated_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    return hours, minutes, seconds, estimated_remaining_dishes

# 主函數
def main():
    create_directories()
    #店家資料CSV，最左邊的COLUMN需放店家ID
    vendor_ids = read_vendor_ids('./a_1.csv')
    crawled_vendors = read_crawled_vendors('./crawled_vendors/crawled_ids.txt')
    total_vendors = len(vendor_ids)
    total_dishes = 0
    product_crawl_times = []
    past_vendor_product_counts = []

    ua = UserAgent()

    for vendor_index, vendor_id in enumerate(vendor_ids):
        if vendor_id in crawled_vendors:
            continue

        start_time_vendor = time.time()  # 開始計時

        try:
            my_headers = {'user-agent': ua.random}
            vendor_data = fetch_vendor_data(vendor_id, my_headers)['data']
            all_dishes_info = process_vendor_data(vendor_id, vendor_data, my_headers) 
            crawled_products = len(all_dishes_info)  
            total_dishes += crawled_products
            past_vendor_product_counts.append(crawled_products)

            # 紀錄該供應商的爬取時間
            crawl_time_vendor = time.time() - start_time_vendor
            product_crawl_times.append(crawl_time_vendor / crawled_products if crawled_products else 0)

            # 保存數據和備份
            save_backup(all_dishes_info, vendor_id)
            write_to_csv('dishes_info.csv', all_dishes_info)
            append_crawled_vendor('./crawled_vendors/crawled_ids.txt', vendor_id)

            # 計算並顯示進度和估計剩餘時間
            hours, minutes, seconds, estimated_remaining_dishes = estimate_remaining_time(
                vendor_index, total_vendors, total_dishes, product_crawl_times, past_vendor_product_counts
            )

            print(f"已爬: {vendor_index+1}/{total_vendors}, "
                  f"此店家爬到: {crawled_products}, "
                  f"已爬了: {total_dishes}個餐點, "
                  f"預估剩餘餐點數量: {int(estimated_remaining_dishes)}, "
                  f"預計剩餘時間: {int(hours)}時{int(minutes)}分{int(seconds)}秒")

        except Exception as e:
            log_error('./error/error_ids.txt', vendor_id, e)

if __name__ == "__main__":
    main()

