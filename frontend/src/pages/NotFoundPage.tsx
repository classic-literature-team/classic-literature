import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-4 py-24 text-center">
      <h1 className="text-6xl font-bold">404</h1>
      <p className="text-muted-foreground">페이지를 찾을 수 없습니다.</p>
      <Button variant="outline" render={<Link to="/" />}>
        홈으로
      </Button>
    </div>
  )
}
