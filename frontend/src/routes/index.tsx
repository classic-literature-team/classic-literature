import { createBrowserRouter } from 'react-router-dom'

import { RootLayout } from '@/layouts/RootLayout'
import { BooksPage } from '@/pages/BooksPage'
import { ChatPage } from '@/pages/ChatPage'
import { HomePage } from '@/pages/HomePage'
import { KeywordSearchPage } from '@/pages/KeywordSearchPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const router = createBrowserRouter([
  // 시안 전체 화면(자체 헤더/네비/푸터 포함)은 RootLayout 밖에서 렌더
  { path: '/', element: <HomePage /> },
  { path: '/chat', element: <ChatPage /> },
  { path: '/search', element: <KeywordSearchPage /> },
  {
    element: <RootLayout />,
    children: [
      { path: 'books', element: <BooksPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
