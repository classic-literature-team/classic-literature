import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

import { apiFetch } from '@/utils/api'

export const bookSchema = z.object({
  id: z.number(),
  title: z.string(),
  author: z.string(),
  year: z.number().nullable(),
})

export type Book = z.infer<typeof bookSchema>

export const bookListSchema = z.array(bookSchema)

export const bookKeys = {
  all: ['books'] as const,
  list: () => [...bookKeys.all, 'list'] as const,
}

async function fetchBooks(): Promise<Book[]> {
  const data = await apiFetch<unknown>('/books')
  return bookListSchema.parse(data)
}

export function useBooks() {
  return useQuery({
    queryKey: bookKeys.list(),
    queryFn: fetchBooks,
  })
}
