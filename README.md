# Atlas Img Parser GUI v2

Tkinter 기반 GUI 프로그램입니다.

이 버전은 **PNG 여러 장 + SpriteInfo.json 한 장** 구조를 지원합니다.
즉, 이제 파싱 단위는 `이미지 1장 + json 1장`이 아니라 **아틀라스 폴더 1개**입니다.

예시:
- `Knight/0.Atlases/`
  - `Knight.png`
  - `Knight Slug Cln.png`
  - `Knight Dream Gate Cln.png`
  - `Spell Effects 2.png`
  - `SpriteInfo.json`

이런 폴더를 통째로 세트로 등록하면 됩니다.

## 기능

- `폴더 세트 추가`: PNG 여러 장 + `SpriteInfo.json` 한 장이 들어 있는 폴더 등록
- `수동 세트 추가`: PNG 여러 장을 직접 고르고, `SpriteInfo.json` 한 장을 고르는 방식도 지원
- 출력 폴더 선택
- 진행률 표시
- 현재 파싱 중인 세트 / 현재 사용하는 아틀라스 / 현재 저장 중인 PNG 표시
- 취소 버튼
- `sxr`, `syr` 기반 padded canvas 적용으로 애니메이션 흔들림 최소화

## 실행

```bash
pip install -r requirements.txt
python main.py
```

## 구조

- `main.py`: Composition Root
- `src/domain`: 엔티티, 이벤트, 인터페이스
- `src/application`: 컨트롤러, 커맨드
- `src/services`: 파싱 핵심 로직, 레코드 팩토리, 레이아웃 전략, 아틀라스 카탈로그 팩토리
- `src/infrastructure`: JSON/이미지 로더, 진행 큐, 백그라운드 실행기
- `src/ui`: Tkinter UI

## 사용된 설계

- **Command Pattern**: 시작/취소 액션 캡슐화
- **Factory Pattern**: JSON -> 레코드, 파일 목록 -> 아틀라스 카탈로그 생성
- **Strategy Pattern**: 흔들림 방지용 캔버스 조립 정책 분리
- **Observer Pattern**: 백그라운드 진행 이벤트를 UI 큐로 전달
- **Dependency Injection**: `main.py`에서 의존성 조립

## 주의

- `SpriteInfo.json`의 `scollectionname` 값과 PNG 파일명(확장자 제외)이 매칭되어야 합니다.
- 기본 회전 복구는 `ROTATE_90` 기준입니다. 특정 세트에서 방향이 이상하면 `src/services/sprite_extractor.py`의 회전 방향만 `ROTATE_270`으로 바꿔 테스트하세요.
