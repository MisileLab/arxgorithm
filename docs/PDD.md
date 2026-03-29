# arxgorithm — Product Design Document

## 개요
arXiv 논문 개인화 추천 오픈소스 웹 플랫폼. 협업 필터링 임베딩 + 에이전틱 추천으로 관심사에 맞는 논문을 찾아줌.

## 문제 정의
- arXiv는 논문 검색에는 좋지만 **개인화 추천이 약함**
- 기존 서비스(Semantic Scholar, Connected Papers)는 폐쇄적이고 셀프호스팅 불가
- 연구자가 자신의 관심사에 맞는 논문을 효율적으로 발견할 방법이 필요

## 타겟 유저
- AI/ML/CS 연구자 및 학생
- arXiv를 정기적으로 읽는 사람
- 특정 분야의 최신 논문을 놓치지 않고 싶은 사람

## 핵심 기능

### 1. 개인화 피드
- 관심 주제/키워드 설정
- 읽은 논문 기반 추천 학습
- 데일리/위클리 추천 이메일 (선택)

### 2. 협업 필터링 임베딩 추천
- 논문 임베딩 생성 (title + abstract 기반)
- 유사도 기반 추천 (코사인 유사도)
- "이 논문을 읽은 사람들이 같이 읽은 논문" 협업 필터링

### 3. 에이전틱 추천
- LLM 에이전트가 유저의 리서치 컨텍스트 파악
- 왜 이 논문을 추천하는지 설명 제공
- 대화형 추천 (채팅 인터페이스)

### 4. 논문 관리
- 북마크 / 읽음 표시 / 폴더
- 메모 및 하이라이트
- 인용 그래프 시각화

### 5. 커뮤니티
- 논문 리뷰 / 토론
- 추천 리스트 공유
- 팔로우 기반 추천

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | React Router v7 |
| Backend | FastAPI (Python) |
| Vector DB | HelixDB |
| Embedding | Sentence Transformers / OpenAI |
| LLM Agent | OpenAI / Anthropic API |
| Crawling | arXiv API + bulk dump |
| Auth | OAuth (Google, GitHub, ORCID) |
| Deploy | Docker + docker-compose |

## 아키텍처

```
[React Router Frontend]
        ↕ REST API
[FastAPI Backend]
   ↕          ↕          ↕
[HelixDB]  [arXiv API]  [LLM Agent]
(vector)   (crawling)   (reasoning)
```

## 데이터 파이프라인
1. arXiv API / bulk dump에서 논문 메타데이터 수집
2. 제목 + 초록으로 임베딩 생성
3. HelixDB에 벡터 저장
4. 유저 상호작용 기반 협업 필터링 매트릭스 업데이트
5. LLM 에이전트로 추천 reasoning 생성

## 오픈소스 전략
- **라이선스**: AGPL-3.0 (셀프호스팅 허용, 수정사항 공유 의무)
- **셀프호스팅**: Docker Compose로 원클릭 배포
- **기여 모델**: GitHub Issues + PR, CODEOWNERS

## 마일스톤

### Phase 1 — MVP (4주)
- [ ] 프로젝트 스캐폴딩 (monorepo 설정)
- [ ] arXiv 크롤러 + 임베딩 파이프라인
- [ ] 기본 검색 + 키워드 기반 추천
- [ ] 회원가입 / 로그인
- [ ] 북마크 기능

### Phase 2 — 개인화 (4주)
- [ ] 협업 필터링 구현
- [ ] 개인화 피드
- [ ] 읽기 히스토리 기반 추천

### Phase 3 — 에이전틱 (4주)
- [ ] LLM 에이전트 통합
- [ ] 대화형 추천 인터페이스
- [ ] 추천 이유 생성

### Phase 4 — 커뮤니티 (4주)
- [ ] 논문 리뷰 / 토론
- [ ] 공개 추천 리스트
- [ ] 팔로우 시스템

## 성공 지표
- DAU / MAU
- 추천 논문 클릭률
- 평균 세션 시간
- 깃허브 스타 수
- 셀프호스팅 인스턴스 수
