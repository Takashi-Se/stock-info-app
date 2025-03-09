# app.pyの先頭部分
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # キャッシュを無効化
from flask import Flask, render_template, request, jsonify
import json
import os
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# お気に入り情報を保存するファイル
FAVORITES_FILE = 'favorites.json'

# お気に入り情報を読み込む
def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"tabs": [{"name": "お気に入り", "stocks": []}]}
    return {"tabs": [{"name": "お気に入り", "stocks": []}]}

# お気に入り情報を保存する
def save_favorites(data):
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 株価情報を取得するクラス
class StockScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
    def get_stock_info(self, code):
        try:
            url = f"https://kabutan.jp/stock/?code={code}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # HTMLを解析
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 会社名を取得
            company_name_element = soup.select_one("div.company_block > h3")
            if not company_name_element:
                return None
                
            company_name = company_name_element.text.strip()
            
            # 現在価格を取得
            price_element = soup.select_one("span.kabuka")
            if not price_element:
                return None
                
            # 円記号と桁区切りのカンマを除去して数値化
            current_price_text = price_element.text.strip()
            current_price_text = current_price_text.replace(',', '').replace('円', '')
            current_price = float(current_price_text)
            
            # 前日比を取得
            diff_element = soup.select_one("dd.yjSt > span.font-size-up")
            if not diff_element:
                diff_element = soup.select_one("dd.yjSt > span.font-size-down")
            
            prev_diff = 0
            prev_diff_percent = 0
            
            if diff_element:
                diff_text = diff_element.text.strip()
                diff_match = re.search(r'([+-]?[\d,]+\.?\d*)円', diff_text)
                if diff_match:
                    prev_diff = float(diff_match.group(1).replace(',', ''))
                
                percent_match = re.search(r'\(([+-]?[\d\.]+)%\)', diff_text)
                if percent_match:
                    prev_diff_percent = float(percent_match.group(1))
            
            return {
                "code": code,
                "name": company_name,
                "current_price": current_price,
                "prev_diff": prev_diff,
                "prev_diff_percent": prev_diff_percent
            }
            
        except Exception as e:
            print(f"株価情報の取得に失敗しました: {e}")
            return None

    def get_stock_url(self, code, site):
        if site == "kabutan":
            return f"https://kabutan.jp/stock/?code={code}"
        elif site == "minkabu":
            return f"https://minkabu.jp/stock/{code}"
        elif site == "yahoo":
            return f"https://finance.yahoo.co.jp/quote/{code}.T"
        else:
            return None

# スクレイパーのインスタンスを作成
scraper = StockScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    code = request.args.get('code', '')
    if not (code.isdigit() and len(code) == 4):
        return jsonify({"error": "証券コードは4桁の数字で入力してください。"})
        
    stock_info = scraper.get_stock_info(code)
    if stock_info:
        return jsonify(stock_info)
    return jsonify({"error": "株価情報の取得に失敗しました。"})

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    return jsonify(load_favorites())

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    data = request.json
    favorites = load_favorites()
    
    # タブインデックスとストック情報を取得
    tab_index = data.get('tab_index', 0)
    stock = data.get('stock', {})
    
    # 該当タブに株価情報を追加
    if 0 <= tab_index < len(favorites["tabs"]):
        # 同じコードの株価情報が既に存在するか確認
        for existing_stock in favorites["tabs"][tab_index]["stocks"]:
            if existing_stock["code"] == stock["code"]:
                return jsonify({"error": "この銘柄は既にお気に入りに登録されています。"})
                
        favorites["tabs"][tab_index]["stocks"].append(stock)
        save_favorites(favorites)
        return jsonify({"success": True})
        
    return jsonify({"error": "お気に入りの追加に失敗しました。"})

@app.route('/api/favorites/remove', methods=['POST'])
def remove_favorite():
    data = request.json
    favorites = load_favorites()
    
    tab_index = data.get('tab_index', 0)
    code = data.get('code', '')
    
    if 0 <= tab_index < len(favorites["tabs"]):
        stocks = favorites["tabs"][tab_index]["stocks"]
        for i, stock in enumerate(stocks):
            if stock["code"] == code:
                del stocks[i]
                save_favorites(favorites)
                return jsonify({"success": True})
                
    return jsonify({"error": "お気に入りの削除に失敗しました。"})

@app.route('/api/favorites/tab', methods=['POST'])
def add_tab():
    data = request.json
    favorites = load_favorites()
    
    name = data.get('name', '新しいタブ')
    
    if len(favorites["tabs"]) >= 10:
        return jsonify({"error": "タブは最大10個までです。"})
        
    favorites["tabs"].append({"name": name, "stocks": []})
    save_favorites(favorites)
    return jsonify({"success": True})

@app.route('/api/favorites/tab/rename', methods=['POST'])
def rename_tab():
    data = request.json
    favorites = load_favorites()
    
    tab_index = data.get('tab_index', 0)
    name = data.get('name', '')
    
    if 0 <= tab_index < len(favorites["tabs"]):
        favorites["tabs"][tab_index]["name"] = name
        save_favorites(favorites)
        return jsonify({"success": True})
        
    return jsonify({"error": "タブ名の変更に失敗しました。"})

@app.route('/api/favorites/tab/remove', methods=['POST'])
def remove_tab():
    data = request.json
    favorites = load_favorites()
    
    tab_index = data.get('tab_index', 0)
    
    if 0 <= tab_index < len(favorites["tabs"]) and len(favorites["tabs"]) > 1:
        del favorites["tabs"][tab_index]
        save_favorites(favorites)
        return jsonify({"success": True})
        
    return jsonify({"error": "タブの削除に失敗しました。最低1つのタブが必要です。"})

@app.route('/api/external_url', methods=['GET'])
def get_external_url():
    code = request.args.get('code', '')
    site = request.args.get('site', '')
    
    if code and site:
        return jsonify({"url": scraper.get_stock_url(code, site)})
    return jsonify({"error": "URLの取得に失敗しました。"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
