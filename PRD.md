1. Project OverviewProject Name: VOC Intelligence PlaygroundObjective: 비정형 고객 리뷰 데이터를 RAG 기반으로 정형화하고, 이를 통계적 지표로 변환하여 실무 부서에 Actionable Insight를 제공하는 자동화 시스템 구축.Key Outcome: 제품 개선 우선순위 도출 및 ROI 중심의 자동 리포팅.2. Technical StackLanguage: Python 3.10+Frontend/UI: StreamlitAI/LLM: LangChain, OpenAI API (GPT-4o) or Claude 3.5 SonnetVector DB: ChromaDB or FAISS (for RAG)Data Analysis: Pandas, Scipy (for $r$, $p$-value)Integration: Slack/Discord Webhook3. Core Functional Requirements3.1 Data Ingestion & PlaygroundCSV, JSON 등 다양한 소스의 리뷰 데이터 로드 기능.Data Source & Filter: 전체 데이터 중 특정 서비스 팀이나 관심 키워드에 맞는 '나만의 데이터셋' 추출 기능.3.2 RAG-based Classification LogicKnowledge Reference: data/docs/ 내의 제품 가이드라인 및 과거 이슈 리스트를 참조.Classification Categories:서비스: [사용자 정의 리스트]유형: [제재, 오류, 개선 사항, 기타]Summary Style: '음슴체' (예: ~함, ~임)를 사용하여 간결하게 요약.3.3 Statistical AnalysisSentiment Scoring: 각 리뷰의 감성 점수 산출 (-1.0 ~ 1.0).Correlation: 감성 점수와 실제 평점(Star Rating) 간의 상관관계($r$) 분석.Significance: 통계적 유의성($p$-value) 검증.Predictive Impact: 특정 기능 개선 시 예상되는 평점 상승 폭 계산.3.4 Automated Reporting & Notification분석 완료 후 지정된 포맷의 Markdown 리포트 생성.config.yaml에 정의된 팀별 매핑 규칙에 따라 특정 이슈 발생 시 Slack/Discord 알림 발송.4. Output Specification (Strict)모든 분석 리포트는 아래 형식을 준수해야 함:Markdown### N [카테고리명] [세부 항목명] 비율%, N건(+변동률%)
- 이슈 요약 : (30자 이내, 음슴체)
- 감정 : 불만, 불신 등 1~2개
- | 불만 유형 | 비율 | 대표 예시 |
  | :--- | :--- | :--- |
  | 유형 A | 00% | "예시 문장" |
- 개선 방향 : 실무적 조치 제안.
5. System Architecture (Folder Structure)Plaintext/
├── app.py                # Streamlit UI & Filter
├── analyzer.py           # RAG Logic & AI Engine
├── statistics_engine.py  # Correlation & Statistical analysis
├── config/
│   └── teams.yaml        # Team mapping & Webhook URLs
├── data/
│   ├── raw/              # Raw VOC data
│   └── vector_store/     # Persistent Vector DB
└── utils/
    └── notifier.py       # Notification module