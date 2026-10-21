---
default_impl: agent
---

# jissp-task-manager 설정

| 키 | 값 | 설명 |
|---|---|---|
| `default_impl` | `agent` \| `skill` \| `inline` | `run` 에서 `--impl` 을 생략했을 때의 구현 방식. 방식별 차이는 [docs/implement.md](docs/implement.md) |

- 서브에이전트 위임을 끄고 기존 방식으로 돌리려면 `default_impl: inline` 으로 바꿉니다.
- 값이 없거나 이 파일이 없으면 `agent` 로 동작합니다.
