import streamlit as st
import pandas as pd
import os
import time

# 1. 페이지 설정 (넓은 화면 유지)
st.set_page_config(page_title="범호마켓 전산시스템", layout="wide", initial_sidebar_state="expanded")

# --- 커스텀 스타일 (폰트, 여백, 타이틀 디자인 최적화) ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* 사이드바 타이틀 및 로고 텍스트 스타일 */
    .sidebar-title {
        font-size: 24px;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0px;
        letter-spacing: -0.5px;
    }
    .sidebar-subtitle {
        font-size: 13px;
        color: #64748b;
        margin-top: -5px;
        margin-bottom: 20px;
        display: block;
    }
    
    /* 본문 헤더 스타일 (이모티콘 없이 깔끔하게) */
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #e2e8f0;
    }
    .sub-header {
        font-size: 18px;
        font-weight: 600;
        color: #334155;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 기본 경로 및 설정
BASE_DIR = r'C:\Users\young jo\Desktop\전산'
FILE_PATH = os.path.join(BASE_DIR, 'orders.csv')
IGNORE_FILE = os.path.join(BASE_DIR, 'ignore_list.txt')
KEYWORD_FILE = os.path.join(BASE_DIR, 'keywords.txt')

# 3. 데이터 로드 및 초기화
if 'df' not in st.session_state:
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH, header=None, names=['이름', '품목', '수량', '주문시간', '주문 상태', '픽업일'], encoding='utf-8-sig')
        df['ID'] = df.groupby('이름').ngroup() + 1
        df['픽업일'] = pd.to_datetime(df['픽업일'], errors='coerce')
        df.insert(0, "선택", False)
        st.session_state.df = df[['선택', 'ID', '이름', '품목', '수량', '주문시간', '주문 상태', '픽업일']]
    else:
        st.session_state.df = pd.DataFrame(columns=['선택', 'ID', '이름', '품목', '수량', '주문시간', '주문 상태', '픽업일'])

# --- 왼쪽 사이드바 네비게이션 ---
with st.sidebar:
    st.markdown("""
        <div>
            <p class="sidebar-title">범호마켓</p>
            <p class="sidebar-subtitle">세종새롬점 관리 시스템</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 이모티콘을 작고 덜 튀는 톤으로 변경
    menu = st.radio(
        "메뉴 이동",
        ["📦 주문 관리", "👥 사용자 관리", "⚙ 키워드 설정", "📊 발주 정산"]
    )
    st.write("---")
    st.caption("Admin Dashboard v1.2")

# ==========================================
# 메뉴 1: 주문 관리
# ==========================================
if menu == "📦 주문 관리":
    st.markdown('<div class="main-header">주문 목록 관리</div>', unsafe_allow_html=True)
    
    # [상단 요약 정보]
    total_orders = len(st.session_state.df)
    total_qty = pd.to_numeric(st.session_state.df['수량'], errors='coerce').sum()
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric(label="총 주문 건수", value=f"{total_orders} 건")
    col_m2.metric(label="총 발주 수량", value=f"{int(total_qty)} 개")
    st.write("")

    # [검색 영역]
    st.markdown('<div class="sub-header">조건 검색</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    s_id = c1.text_input("ID 검색", placeholder="ID 입력")
    s_name = c2.text_input("이름 검색", placeholder="고객명 입력")
    s_item = c3.text_input("품목 검색", placeholder="상품명 입력")
    s_status = c4.selectbox("상태 검색", ["", "미수령", "수령", "픽업일 변경"])
    s_date = c5.date_input("픽업일 검색", value=None)

    filtered_df = st.session_state.df.copy()
    if s_id: filtered_df = filtered_df[filtered_df['ID'].astype(str).str.contains(s_id)]
    if s_name: filtered_df = filtered_df[filtered_df['이름'].str.contains(s_name)]
    if s_item: filtered_df = filtered_df[filtered_df['품목'].str.contains(s_item)]
    if s_status: filtered_df = filtered_df[filtered_df['주문 상태'] == s_status]
    if s_date: filtered_df = filtered_df[filtered_df['픽업일'].dt.date == s_date]

    st.write("---")
    
    # [일괄 수정 및 제어 컨트롤]
    c_btn1, c_btn2, c_btn3, c_space, c_save = st.columns([1, 1, 1.2, 2.5, 1.8])
    with c_btn1:
        if st.button("✔ 전체 선택", use_container_width=True):
            st.session_state.df.loc[filtered_df.index, "선택"] = True
            st.rerun()
    with c_btn2:
        if st.button("✖ 전체 해제", use_container_width=True):
            st.session_state.df.loc[filtered_df.index, "선택"] = False
            st.rerun()
   # [일괄 수정 및 제어 컨트롤] - 삭제 시 ID 재정렬을 위해 수정
    with c_btn3:
        if st.button("🗑 선택 삭제", use_container_width=True):
            st.session_state.df = st.session_state.df[st.session_state.df["선택"] == False].reset_index(drop=True)
            # 삭제 후 ID 재정렬 (이름별 ID 유지 필요 시 별도 처리가 필요하나, 순차번호 원하시면 아래 사용)
            st.session_state.df['ID'] = range(1, len(st.session_state.df) + 1)
            st.rerun()
    with c_save:
        if st.button("저장 (CSV 덮어쓰기)", type="primary", use_container_width=True):
            save_df = st.session_state.df.copy()
            save_df['픽업일'] = save_df['픽업일'].dt.strftime('%Y-%m-%d').replace('nan', '')
            save_df[['이름', '품목', '수량', '주문시간', '주문 상태', '픽업일']].to_csv(FILE_PATH, index=False, header=False, encoding='utf-8-sig')
            st.success("파일 저장 완료!")
            st.rerun()

    with st.expander("🛠 선택한 항목 일괄 변경 도구 (상태/픽업일/수량)"):
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        with b_col1: new_status = st.selectbox("상태 변경", ["", "미수령", "수령", "픽업일 변경"], key="bulk_stat")
        with b_col2: new_date = st.date_input("픽업일 변경", value=None, key="bulk_date")
        with b_col3: new_count = st.number_input("수량 변경", min_value=0, value=0, step=1, key="bulk_cnt")
        with b_col4:
            st.write("") 
            st.write("")
            if st.button("일괄 적용하기", use_container_width=True):
                idx = st.session_state.df[st.session_state.df["선택"] == True].index
                if len(idx) > 0:
                    if new_status: st.session_state.df.loc[idx, "주문 상태"] = new_status
                    if new_date: st.session_state.df.loc[idx, "픽업일"] = pd.to_datetime(new_date)
                    if new_count > 0: st.session_state.df.loc[idx, "수량"] = new_count
                    st.rerun()

    # [주문 추가] - 동일인 ID 유지 로직
    with st.expander("➕ 주문 직접 추가하기"):
        with st.form("add_order_form", clear_on_submit=True):
            f1, f2, f3, f4, f5 = st.columns(5)
            in_name = f1.text_input("이름")
            in_item = f2.text_input("품목")
            in_qty = f3.number_input("수량", 1)
            in_status = f4.selectbox("상태", ["미수령", "수령", "픽업일 변경"])
            in_date = f5.date_input("픽업일", None)
            
            if st.form_submit_button("주문 등록"):
                # 1. 이름이 이미 존재하는지 확인
                existing_entry = st.session_state.df[st.session_state.df['이름'] == in_name]
                
                if not existing_entry.empty:
                    # 기존 이름이 있으면 그 ID를 사용
                    new_id = int(existing_entry.iloc[0]['ID'])
                else:
                    # 없으면 현재 최대 ID + 1
                    new_id = int(st.session_state.df['ID'].max()) + 1 if not st.session_state.df.empty else 1
                
                # 2. 데이터 추가
                new_row = {
                    "선택": False, "ID": new_id, "이름": in_name, "품목": in_item, "수량": in_qty, 
                    "주문시간": time.strftime('%Y-%m-%d %H:%M:%S'), "주문 상태": in_status, 
                    "픽업일": pd.to_datetime(in_date) if in_date else pd.NaT
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.df['픽업일'] = pd.to_datetime(st.session_state.df['픽업일'], errors='coerce')
                st.rerun()

    # [데이터 에디터] (시각적으로만 최근 순 정렬)
    st.caption(f"총 {len(filtered_df)}개의 데이터가 검색되었습니다.")
    display_df = filtered_df.iloc[::-1]
    
    edited_df = st.data_editor(
        display_df, 
        height=600,  #
        hide_index=True, 
        use_container_width=True,
        column_config={
            "주문 상태": st.column_config.SelectboxColumn("주문 상태", options=["미수령", "수령", "픽업일 변경"], required=True),
            "ID": st.column_config.NumberColumn("ID", disabled=True),
            "주문시간": st.column_config.TextColumn("주문시간", disabled=True)
        }
    )
    if not edited_df.equals(display_df): 
        st.session_state.df.update(edited_df)
        st.rerun()

# ==========================================
# 메뉴 2: 메시지 및 사용자 관리
# ==========================================
elif menu == "👥 사용자 관리":
    st.markdown('<div class="main-header">미수령 주문 및 차단 관리</div>', unsafe_allow_html=True)
    if not os.path.exists(IGNORE_FILE): open(IGNORE_FILE, 'w', encoding='utf-8-sig').close()
    
    st.markdown('<div class="sub-header">현재 미수령 고객 목록</div>', unsafe_allow_html=True)
    # 데이터프레임의 인덱스를 보존하면서 정렬
    not_received = st.session_state.df[st.session_state.df['주문 상태'] == '미수령'].sort_values('주문시간', ascending=False)
    
    if not not_received.empty:
        h1, h2, h3, h4, h5 = st.columns([1, 1.5, 0.5, 1.5, 1])
        h1.write("**고객명**"); h2.write("**주문 품목**"); h3.write("**수량**"); h4.write("**주문 접수 시간**"); h5.write("**작업**")
        st.divider()
        
        # enumerate나 iterrows의 idx를 사용해야 키가 겹치지 않습니다.
        for idx, row in not_received.iterrows():
            c1, c2, c3, c4, c5 = st.columns([1, 1.5, 0.5, 1.5, 1])
            c1.write(row['이름'])
            c2.write(row['품목'])
            c3.write(str(row['수량']))
            c4.caption(str(row['주문시간']))
            
            # 핵심: row['ID'] 대신 데이터프레임의 고유 인덱스(idx)를 키로 사용
            if c5.button("차단 등록", key=f"ignore_{idx}"):
                with open(IGNORE_FILE, 'a', encoding='utf-8-sig') as f: f.write(row['이름'] + "\n")
                st.toast(f"{row['이름']} 님이 차단 목록에 추가되었습니다.")
                st.rerun()
    else:
        st.info("현재 미수령 상태인 주문이 없습니다.")

    st.write("---")
    
    st.markdown('<div class="sub-header">현재 차단(무시) 중인 사용자</div>', unsafe_allow_html=True)
    with open(IGNORE_FILE, 'r', encoding='utf-8-sig') as f:
        ignore_users = [line.strip() for line in f.readlines() if line.strip()]
    
    if ignore_users:
        # 중복 제거된 유저 리스트를 돌면서, 인덱스를 키에 포함
        for i, user in enumerate(set(ignore_users)):
            col_a, col_b = st.columns([0.8, 0.2])
            col_a.write(f"▪ {user}")
            # 차단 해제 버튼에도 인덱스(i)를 추가하여 충돌 방지
            if col_b.button("차단 해제", key=f"del_{i}"):
                new_list = [u for u in ignore_users if u != user]
                with open(IGNORE_FILE, 'w', encoding='utf-8-sig') as f: f.write("\n".join(new_list) + "\n")
                st.toast(f"{user} 님 차단 해제 완료")
                st.rerun()
    else:
        st.caption("차단된 사용자가 없습니다.")

# ==========================================
# 메뉴 3: 상품 키워드 관리
# ==========================================
elif menu == "⚙ 키워드 설정":
    st.markdown('<div class="main-header">파싱용 상품 키워드 설정</div>', unsafe_allow_html=True)
    st.caption("크롤러가 텍스트를 인식할 때 사용하는 키워드 패턴입니다.")
    
    keywords_data = []
    if os.path.exists(KEYWORD_FILE):
        with open(KEYWORD_FILE, 'r', encoding='utf-8-sig') as f:
            for line in f.readlines():
                if ',' in line:
                    prod, patterns = line.strip().split(',', 1)
                    keywords_data.append({"품목명": prod, "키워드 패턴": patterns, "활성화": True})
    
    if not keywords_data:
        keywords_data = [{"품목명": "", "키워드 패턴": "", "활성화": True}]
    
    df_keywords = pd.DataFrame(keywords_data)
    
    edited_keywords = st.data_editor(
        df_keywords, 
        key="keyword_editor",
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "품목명": st.column_config.TextColumn("정식 품목명", required=True),
            "키워드 패턴": st.column_config.TextColumn("인식 키워드 패턴 ( | 와 * 사용)", required=True),
            "활성화": st.column_config.CheckboxColumn("사용 여부", default=True)
        }
    )
    
    st.write("")
    if st.button("설정 저장하기", type="primary"):
        with open(KEYWORD_FILE, 'w', encoding='utf-8-sig') as f:
            for _, row in edited_keywords.iterrows():
                if row["활성화"] and str(row["품목명"]).strip() and str(row["키워드 패턴"]).strip():
                    safe_patterns = str(row["키워드 패턴"]).replace(",", "|")
                    f.write(f"{row['품목명']},{safe_patterns}\n")
        st.success("키워드 설정이 저장되었습니다.")
        st.rerun()

# ==========================================
# 메뉴 4: 발주 정산 (완성형)
# ==========================================
elif menu == "📊 발주 정산":
    st.markdown('<div class="main-header">상품별 발주 단가 및 정산</div>', unsafe_allow_html=True)
    
    PRICE_FILE = os.path.join(BASE_DIR, 'price_list.csv')
    
    # 1. 데이터 로드
    if not os.path.exists(PRICE_FILE):
        pd.DataFrame(columns=['품목', '단가', '공구일']).to_csv(PRICE_FILE, index=False, encoding='utf-8-sig')
    
    price_df = pd.read_csv(PRICE_FILE, encoding='utf-8-sig')
    price_df['공구일'] = pd.to_datetime(price_df['공구일'], errors='coerce')
    
    if not st.session_state.df.empty:
        # 주문 데이터와 가격/날짜 데이터 병합
        summary_df = st.session_state.df.groupby('품목', as_index=False)['수량'].sum()
        summary_df = summary_df.merge(price_df, on='품목', how='left')
        
        # 기본값 채우기
        summary_df['단가'] = summary_df['단가'].fillna(0)
        summary_df['전체금액'] = summary_df['수량'] * summary_df['단가']
        
        # --- 검색 및 필터링 ---
        st.markdown('<div class="sub-header">정산 데이터 조회 및 설정</div>', unsafe_allow_html=True)
        col_f, _ = st.columns([1, 2])
        filter_date = col_f.date_input("공구일별 정산 검색 (전체 보려면 비우기)", value=None)
        
        # 에디터용 데이터 (공구일이 맨 오른쪽으로)
        edit_df = summary_df[['품목', '수량', '단가', '전체금액', '공구일']].copy()
        
        # 필터링 적용 (화면 표시용)
        view_df = edit_df.copy()
        if filter_date:
            view_df = view_df[view_df['공구일'].dt.date == filter_date]
        
        # 메트릭 표시 (필터링된 값 기준)
        c1, c2 = st.columns(2)
        c1.metric("대상 품목 수", f"{len(view_df)} 종")
        c2.metric("정산 예상 금액", f"{int(view_df['전체금액'].sum()):,} 원")
        
        # 데이터 에디터
        edited_summary = st.data_editor(
            edit_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "품목": st.column_config.TextColumn("주문 품목", disabled=True),
                "수량": st.column_config.NumberColumn("총 수량", disabled=True),
                "단가": st.column_config.NumberColumn("단가", min_value=0, step=100, format="₩ %d"),
                "전체금액": st.column_config.NumberColumn("전체 합산 금액", disabled=True, format="₩ %d"),
                "공구일": st.column_config.DateColumn("공구일") 
            },
            key="price_editor"
        )
        
        # 변경사항이 있으면 즉시 저장
        if st.session_state.price_editor['edited_rows']:
            # 전체 수정본 반영
            updated_df = edited_summary.copy()
            updated_df['공구일'] = updated_df['공구일'].dt.strftime('%Y-%m-%d')
            updated_df[['품목', '단가', '공구일']].to_csv(PRICE_FILE, index=False, encoding='utf-8-sig')
            st.rerun()

        # CSV 다운로드
        csv_data = edit_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("내역 다운로드 (CSV)", csv_data, '발주_정산_내역.csv', 'text/csv', use_container_width=True)
            
    else:
        st.info("현재 누적된 주문 데이터가 없습니다.")