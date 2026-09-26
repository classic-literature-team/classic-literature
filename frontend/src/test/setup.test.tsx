import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

/**
 * 테스트 인프라(vitest + jsdom + testing-library + jest-dom) 배선 확인용.
 * jsdom 환경에서 렌더가 동작하고 jest-dom 매처가 로드됐는지 검증한다.
 * (후속 6.2/6.3/8.3~8.5 테스트가 이 스택 위에서 실행된다.)
 */
describe('frontend test infra', () => {
  it('renders into jsdom and exposes jest-dom matchers', () => {
    render(<span>근거 패널 테스트 인프라</span>)
    expect(screen.getByText('근거 패널 테스트 인프라')).toBeInTheDocument()
  })
})
