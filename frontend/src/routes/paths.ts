/**
 * 애플리케이션 라우트 경로 상수.
 * 컴포넌트에서 문자열을 하드코딩하지 않고 이 상수를 사용한다.
 */
export const paths = {
  home: '/',
  books: '/books',
} as const

export type AppPath = (typeof paths)[keyof typeof paths]
