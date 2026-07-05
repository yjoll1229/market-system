import time
import pyperclip
import re
import csv
import os
from pywinauto import Desktop
from git import Repo

# 경로 설정
BASE_DIR = r'C:\Users\이영조\Desktop\전산'
ORDER_FILE = os.path.join(BASE_DIR, 'orders.csv')
IGNORE_FILE = os.path.join(BASE_DIR, 'ignore_list.txt')
KEYWORD_FILE = os.path.join(BASE_DIR, 'keywords.txt')
HISTORY_FILE = os.path.join(BASE_DIR, 'processed_ids.txt')

# 1. CSV 저장 및 자동 푸시 함수 (가장 먼저 정의)
def save_to_csv(order):
    with open(ORDER_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            order['name'], order['product'], order['count'], 
            time.strftime('%Y-%m-%d %H:%M:%S'), "미수령", "" 
        ])
    
    try:
        repo = Repo(BASE_DIR)
        repo.git.add(ORDER_FILE)
        repo.index.commit("주문 자동 업데이트")
        repo.remotes.origin.push()
        print(f"저장 및 GitHub 업데이트 완료: {order['name']}")
    except Exception as e:
        print(f"GitHub 업데이트 실패: {e}")

# 2. 무시 목록 읽기
def get_ignore_list():
    if not os.path.exists(IGNORE_FILE): return []
    with open(IGNORE_FILE, 'r', encoding='utf-8-sig') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# 3. 키워드 목록 읽기
def get_menu_rules():
    rules = {}
    if not os.path.exists(KEYWORD_FILE): return rules
    with open(KEYWORD_FILE, 'r', encoding='utf-8-sig') as f:
        for line in f.readlines():
            if ',' in line:
                name, patterns = line.strip().split(',', 1)
                pattern_list = [p.replace('*', '.*') for p in patterns.split('|')]
                rules[name] = pattern_list
    return rules

# 4. 카카오톡 가져오기
def get_kakao_chat_via_clipboard(room_name):
    try:
        app = Desktop(backend="uia")
        win = app.window(title=room_name)
        if not win.exists(): return None
        chat_pane = win.child_window(auto_id="100", control_type="Pane")
        if chat_pane.exists():
            chat_pane.set_focus() 
            time.sleep(0.1)
            chat_pane.type_keys("^a^c")
            time.sleep(0.2)
            return pyperclip.paste()
    except Exception: return None

# 5. 주문 파싱
def parse_order(text):
    menu_rules = get_menu_rules()
    ignore_list = get_ignore_list()
    if re.search(r'http[s]?://', text): return []
    match = re.search(r'\[(.*?)\]\s*\[.*?\]\s*(.*)', text)
    if not match: return []
    name, content = match.groups()
    if name in ignore_list: return []
    num_match = re.search(r'(\d+)', content)
    if not num_match: return []
    count = int(num_match.group(1))
    orders = []
    for product_name, patterns in menu_rules.items():
        if any(re.search(p, content) for p in patterns):
            orders.append({"name": name, "product": product_name, "count": count})
            break 
    return orders

# 6. 기록 관리
def load_processed_ids():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_processed_id(msg_id):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(msg_id + '\n')

# 7. 메인 실행부
if __name__ == "__main__":
    ROOM_NAME = "이영조" 
    print(f"[{ROOM_NAME}] 시스템 시작...")
    processed_msg_ids = load_processed_ids()
    
    while True:
        try:
            current_text = get_kakao_chat_via_clipboard(ROOM_NAME)
            if current_text:
                all_lines = current_text.strip().split('\n')
                for i, line in enumerate(all_lines):
                    msg_id = f"{i}_{line.strip()}"
                    if msg_id not in processed_msg_ids:
                        order_list = parse_order(line)
                        for order in order_list:
                            save_to_csv(order)
                        processed_msg_ids.add(msg_id)
                        save_processed_id(msg_id)
            time.sleep(1)
        except Exception as e:
            print(f"오류 발생: {e}")
            time.sleep(2)
