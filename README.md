# VOC 자동 분석 시스템 (Auto VOC Analyzer)

이 프로젝트는 고객의 소리(VOC, Voice of Customer) 데이터를 자동으로 분류하고 분석하여 인사이트를 도출하는 시스템입니다. Google Gemini (LLM)를 활용하여 리뷰를 요약하고, 감정을 분석하며, 개선 방향을 제안합니다.

## 📌 주요 기능

1.  **Mock 데이터 생성**: 테스트를 위한 가상의 VOC 데이터를 생성합니다. (결제 오류, 앱 튕김, UI 등)
2.  **자동 분류 및 분석**: `config/teams.yaml`에 정의된 키워드를 기반으로 VOC를 팀/카테고리별로 자동 분류합니다.
3.  **LLM 리포트 생성**: Gemini 모델을 사용하여 각 카테고리별로 다음 정보를 포함한 리포트를 생성합니다.
4.  **추적 가능한 분석 시스템**: 모든 분석 요청에 대해 원본 입력, 완성된 프롬프트, AI 응답을 로그로 기록합니다.
5.  **보안 강화**: API Key는 소스 코드에 저장되지 않으며, `.env` 파일을 통해 안전하게 관리됩니다.

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

### 2. 보안 및 API 키 설정 (중요)

이 프로젝트는 보안을 위해 API Key를 코드가 아닌 별도의 환경 설정 파일(`.env`)에서 관리합니다.

1.  프로젝트 루트에 있는 `.env.example` 파일을 복사하여 `.env` 파일로 이름을 변경합니다.
2.  `.env` 파일을 열고 본인의 Google Gemini API Key를 입력합니다.

```ini
# .env 파일 예시
GOOGLE_API_KEY="AIzaSyYourKeyHere..."
```

> **주의**: `.env` 파일은 Git에 업로드되지 않도록 이미 `.gitignore`에 설정되어 있습니다.

## 🚀 사용 방법 (Usage)

### 1단계: 데이터 생성

테스트용 데이터를 생성하려면 다음 명령어를 실행하세요. `data/raw/` 폴더에 `mock_reviews.csv` 파일이 생성됩니다.
(참고: 리포지토리에는 테스트 편의를 위해 기본 `mock_reviews.csv`가 포함되어 있습니다.)

```bash
python generate_data.py
```

### 2단계: 분석 실행 (콘솔 모드)

터미널에서 바로 분석 결과를 확인하려면 다음 명령어를 실행하세요. 분석 과정은 `data/logs/`에 기록됩니다.

```bash
python analyzer.py
```

**로그 확인 방법:**
`data/logs/` 폴더에서 `trace_YYYYMMDD_... .log` 파일을 열어보면, AI에게 실제 전달된 프롬프트와 원본 응답을 확인할 수 있습니다.

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
│   ├── raw/            # 원본 데이터 (mock_reviews.csv 등)
│   ├── processed/      # 분석 완료된 데이터 저장
│   └── logs/           # 분석 추적 로그 (Input/Prompt/Result)
├── utils/              # 유틸리티 모듈
├── analyzer.py         # 핵심 분석 로직 (LangChain + Gemini + Logging)
├── app.py              # Streamlit 웹 애플리케이션 엔트리포인트
├── generate_data.py    # Mock 데이터 생성 스크립트
├── .env.example        # 환경 변수 설정 예시
└── requirements.txt    # 의존성 패키지 목록
```


<!-- LATEST_ANALYSIS_START -->
---
### 🚀 Latest VOC Analysis
> **Update**: 2025-12-30 08:24 | **Project**: `Analysis_20251230_082333` | **Model**: `gemini-2.5-flash`

**Methodology**:
- **RAG Context**: 438 chars loaded.
- **Analysis Count**: 3 categories processed.

**Quick Preview**:
```markdown

### 1 [billing_team] 결제 오류 및 실패 100%, 8 cases
- 이슈 요약 : 결제 오류 및 충전/취소 불가 문제 발생
- 감정 : 불편, 불만
- | 불만 유형 | 비율 | 대표 예시 |
  | :--- | :--- | :--- |
  | payment_error | 100% | "결제 오류 ㅠㅠ 해결 좀 해주세요." |
- 개선 방향 : 결제 시스템 안정성 강화 및 오류 원인 분석 통한 개선 필요


#### 🔍 Analysis Audit (검증 데이터)
| 단계 | 내용 |
| :--- | :--- |
| **Raw Data** | - [payment_error] 페이 충전 실패 ! 해결 좀 해주세요.
- [payment_error] 결제 오류 ㅠㅠ 해결 좀 해주세요.
...
```

👉 **[📄 Click Here to View Full Report](data/processed/Analysis_20251230_082333/report_20251230_082418.md)** 
*(Includes detailed verification trail & logs)*
---
<!-- LATEST_ANALYSIS_END -->