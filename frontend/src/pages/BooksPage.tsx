import { useBooks } from '@/hooks/useBooks'

export function BooksPage() {
  const { data: books, isLoading, isError, error } = useBooks()

  return (
    <div className="mx-auto max-w-2xl py-12">
      <h2 className="mb-6 text-2xl font-semibold">책 목록</h2>

      {isLoading && <p className="text-muted-foreground">불러오는 중...</p>}

      {isError && (
        <p className="text-destructive">
          목록을 불러오지 못했습니다: {error.message}
        </p>
      )}

      {books && books.length === 0 && (
        <p className="text-muted-foreground">등록된 책이 없습니다.</p>
      )}

      {books && books.length > 0 && (
        <ul className="divide-border divide-y rounded-md border">
          {books.map((book) => (
            <li key={book.id} className="p-4">
              <p className="font-medium">{book.title}</p>
              <p className="text-muted-foreground text-sm">
                {book.author}
                {book.year ? ` · ${book.year}` : ''}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
