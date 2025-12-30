# VOC 자동 분석 시스템 (Auto VOC Analyzer)

이 프로젝트는 고객의 소리(VOC, Voice of Customer) 데이터를 자동으로 분류하고 분석하여 인사이트를 도출하는 시스템입니다. Google Gemini (LLM)를 활용하여 리뷰를 요약하고, 감정을 분석하며, 개선 방향을 제안합니다.

## 📌 주요 기능

1.  **Mock 데이터 생성**: 테스트를 위한 가상의 VOC 데이터를 생성합니다. (결제 오류, 앱 튕김, UI 등)
2.  **자동 분류 및 분석**: `config/teams.yaml`에 정의된 키워드를 기반으로 VOC를 팀/카테고리별로 자동 분류합니다.
3.  **LLM 리포트 생성**: Gemini 모델을 사용하여 각 카테고리별로 다음 정보를 포함한 리포트를 생성합니다.
    *   이슈 요약 (음슴체)
    *   주요 감정 키워드
    *   불만 유형 및 비율 (표)
    *   구체적인 개선 방향

## 🛠️ 설치 및 설정 (Installation)

### 1. 환경 설정

Python 3.8 이상의 환경이 필요합니다.

```bash
# 저장소 복제
git clone https://github.com/1916571-alt/auto_VOC.git
cd auto_VOC

# 패키지 설치
pip install -r requirements.txt
```

### 2. API 키 설정

Google Gemini API 사용을 위해 환경 변수를 설정해야 합니다.

**Windows PowerShell:**
```powershell
$env:GOOGLE_API_KEY="your_google_api_key_here"
```

**Mac/Linux:**
```bash
export GOOGLE_API_KEY="your_google_api_key_here"
```

### 3. 카테고리 설정 (선택 사항)

`config/teams.yaml` 파일을 수정하여 분석하고 싶은 팀이나 카테고리, 그리고 관련 키워드를 정의할 수 있습니다.

```yaml
teams:
  Billing_Team:
    keywords: ["결제", "충전", "환불"]
  Tech_Team:
    keywords: ["오류", "버그", "실행"]
```

## 🚀 사용 방법 (Usage)

### 1단계: 데이터 생성

테스트용 데이터를 생성하려면 다음 명령어를 실행하세요. `data/raw/` 폴더에 `mock_reviews.csv` 파일이 생성됩니다.

```bash
python generate_data.py
```

### 2단계: 분석 실행 (콘솔 모드)

터미널에서 바로 분석 결과를 확인하려면 다음 명령어를 실행하세요.

```bash
python analyzer.py
```

### 3단계: 웹 대시보드 실행 (GUI)

Streamlit을 이용한 웹 인터페이스를 실행합니다.

```bash
streamlit run app.py
```

## 📂 폴더 구조

```
auto_VOC/
├── config/             # 설정 파일 디렉토리
│   └── teams.yaml      # 팀별 키워드 정의
├── data/               # 데이터 디렉토리
│   └── raw/            # 생성된 원본 데이터 CSV 저장
├── utils/              # 유틸리티 모듈
├── analyzer.py         # 핵심 분석 로직 (LangChain + Gemini)
├── app.py              # Streamlit 웹 애플리케이션 엔트리포인트
├── generate_data.py    # Mock 데이터 생성 스크립트
└── requirements.txt    # 의존성 패키지 목록
```
