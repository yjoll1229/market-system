import time
import pyperclip
import re
import csv
import os
from pywinauto import Desktop

# 경로 설정
BASE_DIR = r'C:\Users\young jo\Desktop\전산'
ORDER_FILE = os.path.join(BASE_DIR, 'orders.csv')
IGNORE_FILE = os.path.join(BASE_DIR, 'ignore_list.txt')
KEYWORD_FILE = os.path.join(BASE_DIR, 'keywords.txt')
HISTORY_FILE = os.path.join(BASE_DIR, 'processed_ids.txt')  # 기록 파일 추가

# 1. 무시 목록 읽기
def get_ignore_list():
    if not os.path.exists(IGNORE_FILE): return []
    with open(IGNORE_FILE, 'r', encoding='utf-8-sig') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# 2. 키워드 목록 읽기 (동적 로드)
# keywords.txt 형식: 품목명,패턴1|패턴2|패턴3*
def get_menu_rules():
    rules = {}
    if not os.path.exists(KEYWORD_FILE): return rules
    with open(KEYWORD_FILE, 'r', encoding='utf-8-sig') as f:
        for line in f.readlines():
            if ',' in line:
                name, patterns = line.strip().split(',', 1)
                # '*'를 정규식 문법(.*)으로 치환
                pattern_list = [p.replace('*', '.*') for p in patterns.split('|')]
                rules[name] = pattern_list
    return rules

# 3. CSV 저장
def save_to_csv(order):
    with open(ORDER_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            order['name'], order['product'], order['count'], 
            time.strftime('%Y-%m-%d %H:%M:%S'), "미수령", "" 
        ])

# 4. 카카오톡 텍스트 가져오기
def get_kakao_chat_via_clipboard(room_name):
    try:
        app = Desktop(backend="uia")
        win = app.window(title=room_name)
        if not win.exists(): return None
        chat_pane = win.child_window(auto_id="100", control_type="Pane")
        if chat_pane.exists():
            chat_pane.click_input()
            time.sleep(0.1)
            chat_pane.type_keys("^a^c")
            time.sleep(0.2)
            return pyperclip.paste()
    except Exception: return None

# 5. 주문 파싱 (숫자 필수 및 키워드 매칭)
def parse_order(text):
    menu_rules = get_menu_rules()
    ignore_list = get_ignore_list()
    
    lines = text.strip().split('\n')
    orders = []
    for line in lines:
        match = re.search(r'\[(.*?)\]\s*\[.*?\]\s*(.*)', line)
        if match:
            name, content = match.groups()
            
            # 무시 사용자 패스
            if name in ignore_list: continue
            
            # [핵심] 숫자가 반드시 있어야만 주문으로 인정
            num_match = re.search(r'(\d+)', content)
            if not num_match: continue 
            
            count = int(num_match.group(1))
            
            # 키워드 매칭
            for product_name, patterns in menu_rules.items():
                if any(re.search(p, content) for p in patterns):
                    orders.append({"name": name, "product": product_name, "count": count})
                    break 
    return orders

# [추가] 기록 로드 및 저장 함수
def load_processed_ids():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_processed_id(msg_id):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(msg_id + '\n')

# 메인 실행부
if __name__ == "__main__":
    ROOM_NAME = "이영조" 
    print(f"[{ROOM_NAME}] 시스템 시작 및 기록 불러오는 중...")
    
    # 프로그램 시작 시 이전 기록 불러오기
    processed_msg_ids = load_processed_ids()
    print(f"기존 처리된 메시지 {len(processed_msg_ids)}개 로드 완료.")
    
    while True:
        try:
            current_text = get_kakao_chat_via_clipboard(ROOM_NAME)
            
            if current_text:
                all_lines = current_text.strip().split('\n')
                
                for i, line in enumerate(all_lines):
                    # 줄번호와 내용을 합쳐 고유 ID 생성
                    msg_id = f"{i}_{line.strip()}"
                    
                    if msg_id not in processed_msg_ids:
                        # 새로운 메시지인 경우 파싱 및 저장
                        order_list = parse_order(line)
                        for order in order_list:
                            save_to_csv(order)
                            print(f"저장 완료: {order['name']} | {order['product']} | {order['count']}")
                        
                        # 처리 목록에 추가하고 파일에도 즉시 저장
                        processed_msg_ids.add(msg_id)
                        save_processed_id(msg_id)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"오류 발생: {e}")
            time.sleep(2)
