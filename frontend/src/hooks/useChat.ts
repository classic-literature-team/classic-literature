import { useMutation } from '@tanstack/react-query'

import { apiFetch } from '@/utils/api'

interface ChatResponse {
  reply: string
}

async function sendChat(message: string): Promise<string> {
  const data = await apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
  return data.reply
}

/** LLM 대화 전송 mutation. 백엔드 /api/chat 연동. */
export function useChat() {
  return useMutation({
    mutationFn: sendChat,
  })
}
